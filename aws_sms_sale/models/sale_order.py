# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
_logger = logging.getLogger(__name__)

from odoo import api, models, fields
from odoo.exceptions import Warning

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    date_order_send_sms = fields.Datetime(
        string='Fecha envio sms', 
        readonly=True
    )
    
    @api.one    
    def action_custom_send_sms_info_slack(self):
        return True
    
    @api.one
    def action_send_sms_automatic(self, sms_template_id=False, need_check_date_order_send_sms=True):    
        if sms_template_id!=False:
            allow_send_sms = True
            
            if need_check_date_order_send_sms==True and self.date_order_send_sms!=False:
                allow_send_sms = False
                            
            if self.partner_id.mobile==False:
                allow_send_sms = False
                            
            if allow_send_sms==True:
                sms_template_item = self.env['sms.template'].search([('id', '=', sms_template_id)])[0]                                
                sms_compose_message_vals = {
                    'model': 'sale.order',
                    'res_id': self.id,
                    'mobile': self.partner_id.mobile,
                    'sms_template_id': sms_template_id
                }
                
                if self.user_id.id>0:
                    sms_compose_message_obj = self.env['sms.compose.message'].sudo(self.user_id.id).create(sms_compose_message_vals)                
                else:                    
                    sms_compose_message_obj = self.env['sms.compose.message'].sudo().create(sms_compose_message_vals)
                
                return_onchange_sms_template_id = sms_compose_message_obj.onchange_sms_template_id(sms_template_item.id, 'sale.order', self.id)
                
                sms_compose_message_obj.update({
                    'sender': return_onchange_sms_template_id['value']['sender'],
                    'message': return_onchange_sms_template_id['value']['message']                                                     
                })
                sms_compose_message_obj.send_sms_action()
                
                if sms_compose_message_obj.action_send==True:
                    if self.date_order_send_sms==False:                                                                                                                             
                        self.date_order_send_sms = datetime.today()
                        
                    self.action_custom_send_sms_info_slack()#Fix Slack
                    
        return True                    
    
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
            return_valid_phone = self.env['sms.message'].sudo().action_check_valid_phone(self.partner_id.mobile_code_res_country_id, self.partner_id.mobile)
            allow_send = return_valid_phone['valid']
            if allow_send == False:
                raise Warning(return_valid_phone['error'])
        # final
        if allow_send==True:
            ir_model_data = self.env['ir.model.data']
            
            try:
                sms_template_id = ir_model_data.get_object_reference('sms', 'sms_template_id_default_sale_order')[1]
            except ValueError:
                sms_template_id = False            
                                
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'sms_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            
            #default_sender            
            default_sender = 'Todocesped'
            if self.ar_qt_activity_type=='arelux':
                default_sender = 'Arelux'
            elif self.ar_qt_activity_type=='evert':
                default_sender = 'Evert'        
                        
            ctx = dict()
            ctx.update({
                'default_model': 'sale.order',
                'default_res_id': self.ids[0],
                'default_use_template': True,
                'default_sms_template_id': sms_template_id,
                'default_mobile': self.partner_id.mobile,
                'default_sender': default_sender,
                'custom_layout': "sms_arelux.sms_template_data_notification_sms_sale_order"
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