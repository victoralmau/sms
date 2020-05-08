# -*- coding: utf-8 -*-
{
    'name': 'AWS SMS',
    'version': '12.0.1.0.0',    
    'author': 'Odoo Nodriza Tech (ONT)',
    'website': 'https://nodrizatech.com/',
    'category': 'Tools',
    'license': 'AGPL-3',
    'external_dependencies': {
        'python3' : ['boto3', 'phonenumbers', 'urllib'],
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