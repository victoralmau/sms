# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from datetime import datetime
from odoo.exceptions import Warning as UserError


class ShippingExpedition(models.Model):
    _inherit = 'shipping.expedition'

    date_send_sms_info = fields.Datetime(
        string='Date send sms info'
    )

    @api.multi
    def action_send_sms(self):
        self.ensure_one()
        # define
        allow_send = True
        if self.partner_id.opt_out:
            allow_send = False
            raise Warning(_('The client does not accept messages'))
        # action_check_valid_phone
        if allow_send:
            res = self.env['sms.message'].sudo().action_check_valid_phone(
                self.partner_id.mobile_code_res_country_id,
                self.partner_id.mobile
            )
            allow_send = res['valid']
            if not allow_send:
                raise UserError(allow_send['error'])
        # final
        if allow_send:
            ir_model_data = self.env['ir.model.data']

            try:
                sms_template_id = ir_model_data.get_object_reference(
                    'sms',
                    'sms_template_id_default_shipping_expedition'
                )[1]
            except ValueError:
                sms_template_id = False

            try:
                compose_form_id = ir_model_data.get_object_reference(
                    'sms',
                    'sms_template_id_default_shipping_expedition'
                )[1]
            except ValueError:
                compose_form_id = False

            # default_sender
            default_sender = 'Todocesped'
            if self.ar_qt_activity_type == 'arelux':
                default_sender = 'Arelux'
            elif self.ar_qt_activity_type == 'evert':
                default_sender = 'Evert'

            ctx = dict()
            ctx.update({
                'default_model': 'shipping.expedition',
                'default_res_id': self.ids[0],
                'default_use_template': True,
                'default_sms_template_id': sms_template_id,
                'default_mobile': self.partner_id.mobile,
                'default_sender': default_sender,
                'custom_layout':
                    "sms_arelux.sms_template_data_notification_sms_shipping_expedition"
            })
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sms.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }

    @api.multi
    def action_custom_send_sms_info_slack(self):
        return True

    @api.multi
    def action_send_sms_info(self):
        self.ensure_one()
        allow_send = False
        if self.carrier_id.sms_info_sms_template_id:
            if not self.date_send_sms_info:
                if self.carrier_id.send_sms_info:
                    if self.carrier_id.sms_info_sms_template_id:
                        if self.state not in [
                            'error', 'generate', 'canceled',
                            'delivered', 'incidence'
                        ]:
                            if self.carrier_id.carrier_type == 'nacex':
                                allow_send = True
                            else:
                                if self.delegation_name and self.delegation_phone:
                                    allow_send = True
                            # allow_send
                            if allow_send:
                                vals = {
                                    'model': 'shipping.expedition',
                                    'res_id': self.id,
                                    'mobile': self.partner_id.mobile,
                                    'sms_template_id':
                                        self.carrier_id.sms_info_sms_template_id.id
                                }
                                # Fix user_id
                                if self.user_id:
                                    message_obj = self.env['sms.compose.message'].sudo(
                                        self.user_id.id
                                    ).create(vals)
                                else:
                                    message_obj = self.env[
                                        'sms.compose.message'
                                    ].sudo().create(
                                        vals
                                    )

                                res = message_obj.onchange_sms_template_id(
                                    self.carrier_id.sms_info_sms_template_id.id,
                                    'shipping.expedition',
                                    self.id
                                )
                                message_obj.update({
                                    'sender': res['value']['sender'],
                                    'message': res['value']['message']
                                })
                                message_obj.send_sms_action()

                                if message_obj.action_send:
                                    # other
                                    self.date_send_sms_info = datetime.today()
                                    self.action_custom_send_sms_info_slack()

            return True
