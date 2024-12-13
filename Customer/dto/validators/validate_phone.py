import re
from typing import List

import phonenumbers
from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    PhoneNumberType,
    format_number,
    is_valid_number,
    number_type,
    parse as parse_phone_number,
)

MOBILE_NUMBER_TYPES = PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE


def validate_phone(phone):
    if not phone:
        # return phone
        return None

    if not re.fullmatch(r"^(?:[+\d].*\d)$", phone):
        raise ValueError("Phone number must contain only digits or start with a + sign")

    try:
        number = phonenumbers.parse(phone)
        if number.country_code is None:
            raise NumberParseException
    except NumberParseException as e:
        raise ValueError("Please provide a valid mobile phone number") from e

    return phone

    # if not is_valid_number(n) or number_type(n) not in MOBILE_NUMBER_TYPES:
    #     raise ValueError('Please provide a valid mobile phone number')

    # return format_number(n, PhoneNumberFormat.NATIONAL if n.country_code == 233
    # else PhoneNumberFormat.INTERNATIONAL)
