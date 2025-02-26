import base64
import secrets
import string
import uuid
import re
from datetime import datetime, UTC, timedelta, date
from hashlib import md5
import logging

from odoo import fields

from . import settings

ALLOWED_FIELDNAME_CHARS = string.ascii_letters + string.digits + '_'

# Compiled regular expressions
REGEX_HEX16 = re.compile(r'^[0-9a-f]{16}$', re.IGNORECASE)
REGEX_HEX80 = re.compile(r'^[0-9a-f]{80}$', re.IGNORECASE)
REGEX_HEX32 = re.compile(r'^[0-9a-f]{32}$', re.IGNORECASE)
REGEX_LICKEY = re.compile(rf'^{settings.LICENSE_KEY_PREFIX}[0-9a-f]{{32}}$', re.IGNORECASE)
REGEX_OLDKEY = re.compile(r'^geocatbridge-[0-9a-f]{32}$', re.IGNORECASE)  # legacy key format

_logger = logging.getLogger(__name__)


def fix_email_layout_xmlid(layout: str) -> str:
    """ Maps original mail layouts to GeoCat ones, or sets a default. """
    if isinstance(layout, str) and layout.startswith('geocat.'):
        _logger.info(f"Preserving GeoCat email layout '{layout}'")
        return layout
    output = {
        'mail.mail_notification_light': 'geocat.mail_notification_light',
        'mail.mail_notification_layout': 'geocat.mail_notification_layout',
        'mail.mail_notification_invite': 'geocat.mail_notification_invite',
        'mail.mail_notification_layout_with_responsible_signature': 'geocat.mail_notification_layout_with_responsible_signature'
    }.get(layout, 'geocat.mail_notification_layout')
    _logger.info(f"Changed email layout from '{layout}' to '{output}'")
    return output


def force_email_layout_xmlid_kwarg(**kwargs):
    """ Forces the email_layout_xmlid keyword argument to be set to the GeoCat notification layout. """
    email_layout = kwargs.get('email_layout_xmlid')
    kwargs['email_layout_xmlid'] = fix_email_layout_xmlid(email_layout)
    return kwargs


def clamp(n, minimum, maximum):
    """ Clamps the given number between the minimum and maximum values. """
    if n < minimum:
        return minimum
    elif n > maximum:
        return maximum
    else:
        return n


def generate_bridge_key() -> str:
    """ Generates a new GeoCat Bridge license key, e.g. ``GCB26B30E9978BC440FAADE71EFDB1309C4``. """
    return f"{settings.LICENSE_KEY_PREFIX}{uuid.uuid4().hex}".upper()


def default_expiry_date() -> date:
    """ Returns the default expiry date for a new license (one year from now). """
    return fields.Date.today() + timedelta(days=365)


def hashify(*args) -> str:
    """ Returns the MD5 hash as a string for the given concatenated value(s). """
    value = ''.join(str(v) for v in args).encode('ascii', errors='xmlcharrefreplace')
    return md5(value).hexdigest()


def valid_client_token(token: str) -> bool:
    """ Returns true if the given 80-character client token is valid. """
    token = token.zfill(80)[:80]  # Make sure that token is 80 characters long
    timestamp = token[32:-32]
    secret_hash = hashify(timestamp, settings.LICENSE_SECRET_KEY).encode('ascii')
    token_bytes = token.encode('ascii')
    return (secrets.compare_digest(token_bytes[:16], secret_hash[:16]) and
            secrets.compare_digest(token_bytes[-16:], secret_hash[-16:]))


def server_response_token(token: str) -> str:
    """ Generates a MD5 "checksum" based on the client token to add to the license checkout response. """
    return hashify(settings.LICENSE_SECRET_KEY, token)


def split_activation_code(code: str) -> (str, str):
    """ Splits the activation code into a domain and application hash. """
    return code[:16], code[16:]


def encode_license_data(json_data: str) -> bytes:
    """
    Encodes the license data JSON string as base64, and adds a hash to the end.
    The license data is then reversed and a hash of that is added to the end of the reversed string.
    The final string is then encoded as ASCII bytes and returned.

    This process follows the original WHMCS license encoding algorithm.
    """
    try:
        b64_lic_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
        prefixed_data = hashify(datetime.now(UTC), settings.LICENSE_SECRET_KEY) + b64_lic_data
        rev_lic_data = prefixed_data[::-1]
        encoded_lic = rev_lic_data + hashify(rev_lic_data, settings.LICENSE_SECRET_KEY)
        file_bytes = encoded_lic.encode('ascii')
    except Exception as ex:
        raise ValueError("Failed to encode license data") from ex
    return file_bytes
