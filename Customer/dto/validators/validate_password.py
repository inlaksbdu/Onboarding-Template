import re


def validate_password(password):
    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d\W]{8,}$", password):
        raise ValueError(
            "Password must be 8 characters containing at least 1 uppercase letter, "
            "1 lowercase letter and a number "
        )

    return password