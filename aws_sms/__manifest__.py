# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AWS SMS",
    "version": "12.0.1.0.0",
    "author": "Odoo Nodriza Tech (ONT), "
              "Odoo Community Association (OCA)",
    "website": "https://nodrizatech.com/",
    "category": "Tools",
    "license": "AGPL-3",
    "external_dependencies": {
        "python": [
            "boto3",
            "botocore",
            "phonenumbers",
            "unidecode"
        ],
    },
    "depends": [
        "base"
    ],
    "data": [
        "data/ir_cron.xml",
        "views/sms_message_view.xml",
        "wizard/sms_compose_message_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True
}
