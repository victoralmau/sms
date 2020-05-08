# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import api, models, fields

class SmsTemplate(models.Model):
    _inherit = 'sms.template'
    
    sender = fields.Selection(
        [
            ('Todocesped', 'Todocesped'),
            ('Arelux', 'Arelux'),
            ('Evert', 'Evert'),        
        ],
        size=15, 
        string='Sender default', 
        default='Todocesped'
    )