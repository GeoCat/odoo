import base64
import secrets
import string
import uuid
import re
from datetime import datetime, UTC, timedelta, date
from hashlib import md5
import logging
from pathlib import Path

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


def module_base_path() -> Path:
    """ Returns the base path of the GeoCat module. """
    return Path(__file__).resolve().parent.parent


def map_email_layout_template(layout_template, force_default: bool = False) -> str:
    """ Maps original Odoo mail layouts to GeoCat ones, or sets a GeoCat template as the default if not mapped but forced.
        Note that the GeoCat layouts are standalone and do not inherit from the original Odoo ones!
    """
    if isinstance(layout_template, str) and layout_template.startswith('geocat.'):
        # Already a GeoCat layout: keep it that way
        return layout_template

    # NOTE: The mapping below works for Odoo 18 but may have to be adjusted for future versions!   TODO: add tests!!
    forced_template = {
        'mail.mail_notification_light': 'geocat.mail_layout_light',
        'mail.mail_notification_layout': 'geocat.mail_layout_master',
        'mail.mail_notification_invite': 'geocat.mail_layout_invite',
        'mail.mail_notification_layout_with_responsible_signature': 'geocat.mail_layout_master_with_responsible_signature'
    }.get(layout_template)

    if not forced_template:
        if not force_default:
            # No mapping found and we don't want to force a default: return the input value
            return layout_template

        # The layout template was set to False, or no mapping was found (forced_template = None): prefer light template
        forced_template = 'geocat.mail_layout_light'

        if isinstance(layout_template, str):
            # Special case where the mapping is not exact
            if 'with_responsible_signature' in layout_template:
                # The template appears to be some override of the master layout with responsible signature
                forced_template = 'geocat.mail_layout_master_with_responsible_signature'

            # Log that we are overriding an unmapped template
            _logger.info(f"Requested mail layout template '{layout_template}' has not been mapped: applying default '{forced_template}'")

    return forced_template


def set_email_layout_xmlid_kwarg(arg_dict: dict) -> dict:
    """ Adds the email_layout_xmlid keyword argument (if missing) and
    sets it to an appropriate GeoCat email layout template.

    Note that the email_layout_xmlid is not enforced if the message type is 'email' and no layout was specified,
    to avoid adding GeoCat footers to every email (response) in the thread.

    The argument dictionary is manipulated in-place but also returned.
    """
    if not arg_dict:
        # Some arguments may have been set to 'False', so then the getter would fail.
        # There's nothing to evaluate also, so we just return whatever arg_dict is.
        return arg_dict

    message_type = arg_dict.get('message_type')
    email_layout = arg_dict.get('email_layout_xmlid')
    if message_type == 'email' and not email_layout:
        # If the message type is 'email' and no email layout is set, we won't add it:
        # otherwise we will keep adding more GeoCat footers to the thread.
        return arg_dict

    # Set the email layout XML ID if not already set
    arg_dict['email_layout_xmlid'] = map_email_layout_template(email_layout, True)
    return arg_dict


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
    Finally, the resulting string is encoded as ASCII bytes and returned.

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
