# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'AWS SMS',
    'version': '10.0.1.0.0',    
    'author': 'Odoo Nodriza Tech (ONT)',
    'website': 'https://nodrizatech.com/',
    'category': 'Tools',
    'license': 'AGPL-3',
    'external_dependencies': {
        'python' : ['boto3', 'phonenumbers'],
    },
    'depends': ['base'],
    'data': [
        'data/ir_cron.xml',
        'views/sms_message_view.xml',
        'wizard/sms_compose_message_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,    
}