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


def map_email_layout_template(template_name: str) -> str:
    """ Maps original Odoo mail layouts to GeoCat ones, or sets the "light" template as the default.
        Note that the GeoCat layouts are standalone and do not inherit from the original Odoo ones!
    """
    if isinstance(template_name, str) and template_name.startswith('geocat.'):
        # Already a GeoCat layout: keep it that way
        return template_name

    # NOTE: The mapping below works for Odoo 18 but may have to be adjusted for future versions!
    output = {
        'mail.mail_notification_light': 'geocat.mail_layout_light',
        'mail.mail_notification_layout': 'geocat.mail_layout_master',
        'mail.mail_notification_invite': 'geocat.mail_layout_invite',
        'mail.mail_notification_layout_with_responsible_signature': 'geocat.mail_layout_master_with_responsible_signature'
    }.get(template_name)

    if not output:
        # There was no template name, or it was not found in the mapping
        output = 'geocat.mail_layout_light'
        if template_name:
            _logger.info(f"Requested mail layout template '{template_name}' has not been mapped: returning default '{output}'")

    return output


def force_email_layout_xmlid_kwarg(**kwargs):
    """ Adds the email_layout_xmlid keyword argument (if missing) and
    sets it to an appropriate GeoCat email layout template. """
    email_layout = kwargs.get('email_layout_xmlid')
    kwargs['email_layout_xmlid'] = map_email_layout_template(email_layout)
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


def format_bridge_key(key: str) -> str:
    """ Formats the given license key in a more human-readable way (break into parts of 5 chars). """
    return '-'.join([key[i:i + 5] for i in range(0, 35, 5)])


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
