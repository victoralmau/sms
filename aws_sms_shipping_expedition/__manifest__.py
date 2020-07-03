# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'AWS SMS Shipping Expedition',
    'version': '10.0.1.0.0',    
    'author': 'Odoo Nodriza Tech (ONT)',
    'website': 'https://nodrizatech.com/',
    'category': 'Tools',
    'license': 'AGPL-3',
    'depends': ['base', 'aws_sms', 'shipping_expedition'],
    'data': [
        'views/shipping_expedition_view.xml',
    ],
    'installable': True,
    'auto_install': False,    
}