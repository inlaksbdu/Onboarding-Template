import re

import phonenumbers
from phonenumbers import (
    NumberParseException,
    PhoneNumberType,
)


def validate_password(password):
    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d\W]{8,}$", password):
        raise ValueError(
            "Password must be 8 characters containing at least 1 uppercase letter, "
            "1 lowercase letter and a number "
        )

    return password


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
