# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning as UserError
import copy
import datetime
import unicode

from werkzeug import urls
from functools import reduce

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
        if fields is None:
            fields = ['message']

        res_ids_to_templates = self.get_sms_template(res_ids)

        # templates: res_id -> template; template -> res_ids
        templates_to_res_ids = {}
        for res_id, template in res_ids_to_templates.iteritems():
            templates_to_res_ids.setdefault(template, []).append(res_id)

        results = dict()
        for template, template_res_ids in templates_to_res_ids.iteritems():
            Template = self.env['sms.template']
            # generate fields value for all res_ids linked to the current template
            if template.lang:
                Template = Template.with_context(lang=template._context.get('lang'))
            for field in fields:
                Template = Template.with_context(safe=field in {'sender'})
                generated_field_values = Template.render_template(
                    getattr(template, field),
                    template.model_id,
                    template_res_ids,
                    post_process=(field == 'message')
                )
                for res_id, field_value in generated_field_values.iteritems():
                    results.setdefault(res_id, dict())[field] = field_value
            # update values for all res_ids
            for res_id in template_res_ids:
                values = results[res_id]
                if values.get('message'):
                    values['message'] = tools.html_sanitize(values['message'])
                # technical settings
                values.update(
                    model_id=template.model_id,
                    res_id=res_id or False
                )

        return multi_mode and results or results[res_ids[0]]

    @api.model
    def render_template(self, template_txt, model_id, res_ids, post_process=False):
        multi_mode = True
        results = dict.fromkeys(res_ids, u"")
        # fix
        if isinstance(model_id, str) or isinstance(model_id, unicode):
            model_id = self.env['ir.model'].search([('model', '=', model_id)])[0]
        # try to load the template
        try:
            ctx = self.env.context
            mako_env = \
                mako_safe_template_env if ctx.get('safe') else mako_template_env
            template = mako_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.info("Failed to load template %r", template_txt, exc_info=True)
            return multi_mode and results or results[res_ids[0]]

        # prepare template variables
        records = self.env[model_id.model].browse(filter(None, res_ids))
        res_to_rec = dict.fromkeys(res_ids, None)
        for record in records:
            res_to_rec[record.id] = record

        variables = {
            'user': self.env.user,
            'ctx': self._context,  # context kw would clash with mako internals
        }
        for res_id, record in res_to_rec.iteritems():
            variables['object'] = record
            try:
                render_result = template.render(variables)
            except Exception:
                _logger.info(
                    "Failed to render template %r using values %r"
                    % (
                        template,
                        variables
                    ), exc_info=True
                )
                raise UserError(
                    _("Failed to render template %r using values %r")
                    % (
                        template,
                        variables
                    )
                )
            if render_result == u"False":
                render_result = u""
            results[res_id] = render_result

        if post_process:
            for res_id, result in results.iteritems():
                results[res_id] = result

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
