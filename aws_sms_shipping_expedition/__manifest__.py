# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AWS SMS Shipping Expedition",
    "version": "12.0.1.0.0",
    "author": "Odoo Nodriza Tech (ONT), "
              "Odoo Community Association (OCA)",
    "website": "https://nodrizatech.com/",
    "category": "Tools",
    "license": "AGPL-3",
    "depends": [
        "base",
        "aws_sms",
        "shipping_expedition"  # https://github.com/OdooNodrizaTech/stock
    ],
    "data": [
        "views/shipping_expedition_view.xml",
    ],
    "installable": True
}
