# -*- coding: utf-8 -*-
from odoo import _, api, exceptions, fields, models
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class ShippingExpedition(models.Model):
    _inherit = 'shipping.expedition'        
    
    date_send_sms_info = fields.Datetime(
        string='Fecha SMS info'
    )
    
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

    @api.one
    def action_generate_shipping_expedition_link_tracker(self):
        return super(ShippingExpedition, self).action_generate_shipping_expedition_link_tracker()