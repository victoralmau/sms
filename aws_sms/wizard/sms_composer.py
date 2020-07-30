# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class SmsComposer(models.TransientModel):
    _name = 'sms.composer'
    _inherit = 'sms.compose.message'
    _description = 'SMS composition wizard'

    @api.model
    def default_get(self, fields):
        result = super(SmsComposer, self).default_get(fields)

        # v6.1 compatibility mode
        result['model'] = result.get('model', self._context.get('active_model'))
        result['res_id'] = result.get('res_id', self._context.get('active_id'))

        vals = {}
        for field in vals:
            if field in fields:
                result[field] = vals[field]

        # TDE HACK: as mailboxes used default_model='res.users' and default_res_id=uid
        # (because of lack of an accessible pid), creating a message on its own
        # profile may crash (res_users does not allow writing on it)
        # Posting on its own profile works (res_users redirect to res_partner)
        # but when creating the mail.message to create the mail.compose.message
        # access rights issues may rise
        # We therefore directly change the model and res_id
        if result['model'] == 'res.users' and result['res_id'] == self._uid:
            result['model'] = 'res.partner'
            result['res_id'] = self.env.user.partner_id.id

        if fields is not None:
            [result.pop(field, None) for field in result.keys() if field not in fields]
        return result

    @api.multi
    def get_message_values(self, res_ids):
        self.ensure_one()
        results = dict.fromkeys(res_ids, False)
        # compute alias-based reply-to in batch
        for res_id in res_ids:
            # static wizard (sms.message) values
            sms_values = {
                'sender': self.sender,
                'message': self.message or '',
            }
            results[res_id] = sms_values
        return results
