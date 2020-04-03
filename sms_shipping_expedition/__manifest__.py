# -*- coding: utf-8 -*-
{
    'name': 'SMS Shipping Expedition',
    'version': '10.0.1.0.0',    
    'author': 'Odoo Nodriza Tech (ONT)',
    'website': 'https://nodrizatech.com/',
    'category': 'Tools',
    'license': 'AGPL-3',
    'depends': ['base', 'sms', 'shipping_expedition'],
    'data': [
        'views/shipping_expedition_view.xml',
    ],
    'installable': True,
    'auto_install': False,    
}