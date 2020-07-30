# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# https://docs.aws.amazon.com/sns/latest/dg/sms_stats_usage.html
from odoo import api, fields, models, tools, _
import boto3
from botocore.exceptions import ClientError

from urllib.request import urlopen
import gzip
import io
import unidecode

import logging

import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type
_logger = logging.getLogger(__name__)


class SmsMessage(models.Model):
    _name = 'sms.message'
    _description = 'SMS Message'
    _rec_name = 'message_id'

    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country'
    )
    mobile = fields.Char(
        string='Mobile'
    )
    message = fields.Text(
        string='Message'
    )
    sender = fields.Char(
        string='Sender'
    )
    message_id = fields.Char(
        string='Message Id'
    )
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model'
    )
    res_id = fields.Integer(
        string='Related Document ID'
    )
    state = fields.Selection(
        selection=[
            ('delivery', 'Delivery'),
            ('failed', 'Failed'),
        ],
        default='delivery',
        string='State',
    )
    delivery_status = fields.Char(
        string='Delivery Status'
    )
    price = fields.Float(
        string='Price'
    )
    part_number = fields.Integer(
        string='Part Number'
    )
    total_parts = fields.Integer(
        string='Total Parts'
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User id'
    )

    @api.model
    def create(self, values):
        # replace accents unidecode
        if 'message' in values:
            values['message'] = unidecode.unidecode(values['message'])

        return super(SmsMessage, self).create(values)

    @api.multi
    def action_send_error_sms_message_message_slack(self, res):
        return

    @api.model
    def action_check_valid_phone(self, country_id, mobile):
        return_item = {
            'error': '',
            'valid': True
        }
        # check mobile
        if not mobile or mobile is None:
            return_item['valid'] = False
            return_item['error'] = _('It is necessary to define a mobile')
        # check_country_code
        if country_id.id == 0:
            return_item['valid'] = False
            return_item['error'] = _('The prefix is NOT defined')
        # check prefix in phone
        if mobile:
            if '+' in mobile:
                return_item['valid'] = False
                return_item['error'] = \
                    _('The prefix must NOT be defined in the mobile')
        # phonenumbers
        if return_item['valid']:
            number_to_check = '+' + str(country_id.phone_code) + str(mobile)
            number_to_check = '+%s%s' % (
                country_id.phone_code,
                mobile
            )
            try:
                return_is_mobile = carrier._is_mobile(
                    number_type(
                        phonenumbers.parse(
                            number_to_check,
                            country_id.code
                        )
                    )
                )
                if not return_is_mobile:
                    return_item['valid'] = False
                    return_item['error'] = _('The mobile is not valid')
            except phonenumbers.NumberParseException:
                return_item['valid'] = False
                return_item['error'] = \
                    _('The phone is not valid (NumberParseException)')
        # return
        return return_item

    @api.multi
    def action_check_valid(self):
        self.ensure_one()
        return self.action_check_valid_phone(
            self.country_id,
            self.mobile
        )

    @api.multi
    def action_send_real(self):
        self.ensure_one()
        # Create an SNS client
        AWS_ACCESS_KEY_ID = tools.config.get('aws_access_key_id')
        AWS_SECRET_ACCESS_KEY = tools.config.get('aws_secret_key_id')
        AWS_SMS_REGION_NAME = tools.config.get('aws_region_name')

        try:
            res_return = {
                'send': True,
                'error': ''
            }
            client = boto3.client(
                "sns",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_SMS_REGION_NAME
            )
            # Send your sms message.
            phone_number_full = "+%s%" % (
                self.country_id.phone_code,
                self.mobile
            )
            response = client.publish(
                PhoneNumber=phone_number_full,
                Message=str(self.message),
                # Sender=self.sender
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': self.sender
                    }
                }
            )
            # Fix MessageId
            if 'MessageId' in response:
                self.message_id = response['MessageId']
            else:
                res_return['send'] = False
                res_return['error'] = response

            return res_return
        except ClientError as e:
            res_return = {
                'send': False,
                'error': ''
            }
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                res_return['error'] = _("User already exists")
            else:
                # res_return['error'] = e
                res_return['error'] = _('Client error')

            return res_return

    @api.multi
    def action_send(self):
        self.ensure_one()
        if 'False' in self.message:
            res_to_slack = {
                'send': False,
                'error': _('The message contains False')
            }
            self.state = 'failed'
            self.action_send_error_sms_message_message_slack(
                res_to_slack
            )
            return False
        else:
            return_action = self.action_send_real()
            # Fix list
            if isinstance(return_action, (list,)):
                return_action = return_action[0]
                if isinstance(return_action, (list,)):
                    return_action = return_action[0]
            # slack_message
            if not return_action['send']:
                res_to_slack = return_action
                self.state = 'failed'
                self.action_send_error_sms_message_message_slack(
                    res_to_slack
                )
            return return_action['send']

    def s3_line_sms_message(self, line):
        line_split = line.split(',')
        sms_message_ids = self.env['sms.message'].search(
            [
                ('message_id', '=', line_split[1])
            ]
        )
        if sms_message_ids:
            sms_message_id = sms_message_ids[0]
            if not sms_message_id.price:
                # state
                delivery_status = line_split[4]
                if "accepted" not in delivery_status:
                    sms_message_id.state = 'failed'
                # other_fields
                sms_message_id.delivery_status = line_split[4]
                sms_message_id.price = line_split[5]
                sms_message_id.part_number = line_split[6]
                sms_message_id.total_parts = line_split[7]

    @api.model
    def cron_sms_usage_reports(self):
        AWS_ACCESS_KEY_ID = tools.config.get('aws_access_key_id')
        AWS_SECRET_ACCESS_KEY = tools.config.get('aws_secret_key_id')
        bucket_sms_report = 'sms-report-arelux'
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name='eu-west-1'
        )
        all_objects = s3.list_objects(Bucket=bucket_sms_report)
        if len(all_objects['Contents']) > 0:
            for content in all_objects['Contents']:
                obj = s3.get_object(
                    Bucket=bucket_sms_report,
                    Key=content['Key']
                )
                obj_gzip = False

                if obj['ContentType'] == 'text/plain':
                    if 'ContentEncoding' in obj:
                        if obj['ContentEncoding'] == 'gzip':
                            obj_gzip = True

                            return_presigned_url = s3.generate_presigned_url(
                                'get_object',
                                Params={
                                    'Bucket': bucket_sms_report,
                                    'Key': content['Key']
                                },
                                ExpiresIn=100
                            )
                            page = urlopen(return_presigned_url)
                            gzip_filehandle = gzip.GzipFile(
                                fileobj=io.BytesIO(page.read())
                            )
                            content_file = gzip_filehandle.readlines()
                            count_lines = 0
                            for content_file_line in content_file:
                                if count_lines > 0:
                                    self.s3_line_sms_message(content_file_line)

                                count_lines += 1
                    # read_file
                    if not obj_gzip:
                        count_lines = 0
                        for line in obj['Body']._raw_stream:
                            if count_lines > 0:
                                self.s3_line_sms_message(line)

                            count_lines += 1
