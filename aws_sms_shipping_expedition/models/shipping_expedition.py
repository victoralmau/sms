# -*- coding: utf-8 -*-
from odoo import _, api, exceptions, fields, models
from datetime import datetime
from odoo.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)

class ShippingExpedition(models.Model):
    _inherit = 'shipping.expedition'        
    
    date_send_sms_info = fields.Datetime(
        string='Fecha SMS info'
    )

    @api.multi
    def action_send_sms(self):
        '''
        This function opens a window to compose an sms, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        # define
        allow_send = True
        if allow_send == True and self.partner_id.opt_out == True:
            allow_send = False
            raise Warning("El cliente no acepta mensajes")
        # action_check_valid_phone
        if allow_send == True:
            return_valid_phone = self.env['sms.message'].sudo().action_check_valid_phone(
                self.partner_id.mobile_code_res_country_id, self.partner_id.mobile)
            allow_send = return_valid_phone['valid']
            if allow_send == False:
                raise Warning(allow_send['error'])
        # final
        if allow_send == True:
            ir_model_data = self.env['ir.model.data']

            try:
                sms_template_id = ir_model_data.get_object_reference('sms', 'sms_template_id_default_shipping_expedition')[1]
            except ValueError:
                sms_template_id = False

            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'sms_template_id_default_shipping_expedition')[1]
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
                'custom_layout': "sms_arelux.sms_template_data_notification_sms_shipping_expedition"
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

    @api.one    
    def action_custom_send_sms_info_slack(self):
        return True

    @api.one
    def action_send_sms_info(self):
        allow_send = False
        if self.carrier_id.sms_info_sms_template_id.id > 0:
            if self.date_send_sms_info == False:
                if self.carrier_id.send_sms_info == True:
                    if self.carrier_id.sms_info_sms_template_id != False:
                        if self.state not in ['error', 'generate', 'canceled', 'delivered', 'incidence']:
                            if self.partner_id.mobile != False and self.partner_id.mobile_code_res_country_id != False:
                                if self.carrier_id.carrier_type == 'nacex':
                                    allow_send = True
                                else:
                                    if self.delegation_name != False and self.delegation_phone != False:
                                        allow_send = True
                            # allow_send
                            if allow_send == True:
                                _logger.info('Enviamos el SMS respecto a la expedicion ' + str(self.id))
                                sms_compose_message_vals = {
                                    'model': 'shipping.expedition',
                                    'res_id': self.id,
                                    'country_id': self.partner_id.mobile_code_res_country_id.id,
                                    'mobile': self.partner_id.mobile,
                                    'sms_template_id': self.carrier_id.sms_info_sms_template_id.id
                                }
                                # Fix user_id
                                if self.user_id.id > 0:
                                    sms_compose_message_obj = self.env['sms.compose.message'].sudo(
                                        self.user_id.id).create(sms_compose_message_vals)
                                else:
                                    sms_compose_message_obj = self.env['sms.compose.message'].sudo().create(
                                        sms_compose_message_vals)

                                return_onchange_sms_template_id = sms_compose_message_obj.onchange_sms_template_id(
                                    self.carrier_id.sms_info_sms_template_id.id, 'shipping.expedition', self.id)

                                sms_compose_message_obj.update({
                                    'sender': return_onchange_sms_template_id['value']['sender'],
                                    'message': return_onchange_sms_template_id['value']['message']
                                })
                                sms_compose_message_obj.send_sms_action()

                                if sms_compose_message_obj.action_send == True:
                                    # other
                                    self.date_send_sms_info = datetime.today()
                                    self.action_custom_send_sms_info_slack()  # Fix Slack

            return True