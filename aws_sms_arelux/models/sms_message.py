# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import api, models, fields

class SmsMessage(models.Model):
    _inherit = 'sms.message'

    @api.one
    def action_send_real(self):
        #override sender
        if self.model_id.id>0 and self.res_id>0:
            model_item_ids = self.env[self.model_id.model].sudo().search([('id', '=', self.res_id)])
            if len(model_item_ids)>0:
                model_item_id = model_item_ids[0]
                if 'ar_qt_activity_type' in model_item_id:
                    if model_item_id['ar_qt_activity_type']=='todocesped':
                        self.sender = 'Todocesped'
                    elif model_item_id['ar_qt_activity_type']=='arelux':
                        self.sender = 'Arelux'
        #return
        return super(SmsMessage, self).action_send_real()