# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import copy
import datetime

from werkzeug import urls
import functools
import dateutil.relativedelta as relativedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning as UserError
from odoo.tools import pycompat

import logging
_logger = logging.getLogger(__name__)

try:
    # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment
    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,               # do not output newline after blocks
        autoescape=True,                # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,

        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw : relativedelta.relativedelta(*a, **kw),
    })
    mako_safe_template_env = copy.copy(mako_template_env)
    mako_safe_template_env.autoescape = False
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class SmsTemplate(models.Model):
    _name = 'sms.template'
    _description = 'SMS Plantilla'

    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Modelo'
    )
    name = fields.Char(
        string='Nombre'
    )
    sender = fields.Char(
        string='Sender default'
    )
    message = fields.Text(
        string='Contenido'
    )
    lang = fields.Char(
        string='Idioma',
        placeholder="${object.partner_id.lang}"
    )

    @api.multi
    def generate_sms(self, res_ids, fields=None):
        self.ensure_one()
        multi_mode = True
        if isinstance(res_ids, pycompat.integer_types):
            res_ids = [res_ids]
            multi_mode = False
        if fields is None:
            fields = ['body_html']

        res_ids_to_templates = self.get_email_template(res_ids)
        # templates: res_id -> template; template -> res_ids
        templates_to_res_ids = {}
        for res_id, template in res_ids_to_templates.items():
            templates_to_res_ids.setdefault(template, []).append(res_id)

        results = dict()
        for template, template_res_ids in templates_to_res_ids.items():
            Template = self.env['sms.template']
            # generate fields value for all res_ids linked to the current template
            if template.lang:
                Template = Template.with_context(
                    lang=template._context.get('lang')
                )
            for field in fields:
                Template = Template.with_context(safe=field in {'subject'})
                generated_field_values = Template._render_template(
                    getattr(template, field), template.model, template_res_ids,
                    post_process=(field == 'body_html'))
                for res_id, field_value in generated_field_values.items():
                    results.setdefault(res_id, dict())[field] = field_value
            # update values for all res_ids
            for res_id in template_res_ids:
                values = results[res_id]
                # body: add user signature, sanitize
                if 'body_html' in fields and template.user_signature:
                    signature = self.env.user.signature
                    if signature:
                        values['body_html'] = tools.append_content_to_html(
                            values['body_html'],
                            signature,
                            plaintext=False
                        )
                if values.get('body_html'):
                    values['message'] = tools.html_sanitize(
                        values['body_html']
                    )
                # technical settings
                values.update(
                    model=template.model,
                    res_id=res_id or False,
                )

        return multi_mode and results or results[res_ids[0]]

    @api.model
    def _render_template(self, template_txt, model, res_ids, post_process=False):
        """ Render the given template text, replace mako expressions ``${expr}``
        with the result of evaluating these expressions with an evaluation
        context containing:
         - ``user``: Model of the current user
         - ``object``: record of the document record this mail is related to
         - ``context``: the context passed to the mail composition wizard
        :param str template_txt: the template text to render
        :param str model: model name of the document record this mail is related to.
        :param int res_ids: list of ids of document records those mails are related to.
        """
        multi_mode = True
        if isinstance(res_ids, pycompat.integer_types):
            multi_mode = False
            res_ids = [res_ids]

        results = dict.fromkeys(res_ids, u"")

        # try to load the template
        try:
            mako_env = mako_safe_template_env \
                if self.env.context.get('safe') else mako_template_env
            template = \
                mako_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.info("Failed to load template %r", template_txt, exc_info=True)
            return multi_mode and results or results[res_ids[0]]

        # prepare template variables
        records = self.env[model].browse(it for it in res_ids if it)
        res_to_rec = dict.fromkeys(res_ids, None)
        for record in records:
            res_to_rec[record.id] = record
        variables = {
            'user': self.env.user,
            'ctx': self._context,  # context kw would clash with mako internals
        }
        for res_id, record in res_to_rec.items():
            variables['object'] = record
            try:
                render_result = template.render(variables)
            except Exception as e:
                _logger.info(
                    _("Failed to render template %r using values %r")
                    % (template, variables),
                    exc_info=True
                )
                raise UserError(
                    _("Failed to render template %r using values %r")
                    % (template, variables) + "\n\n%s: %s"
                    % (type(e).__name__, str(e))
                )
            if render_result == u"False":
                render_result = u""
            results[res_id] = render_result

        if post_process:
            for res_id, result in results.items():
                results[res_id] = self.render_post_process(result)

        return multi_mode and results or results[res_ids[0]]

    @api.multi
    def get_sms_template(self, res_ids):
        multi_mode = True
        if res_ids is None:
            res_ids = [None]
        results = dict.fromkeys(res_ids, False)

        if not self.ids:
            return results
        self.ensure_one()

        langs = self.render_template(self.lang, self.model_id, res_ids)
        for res_id, lang in langs.iteritems():
            if lang:
                template = self.with_context(lang=lang)
            else:
                template = self
            results[res_id] = template

        return multi_mode and results or results[res_ids[0]]
