"""
password_generator.py
----------------------
Generates strong random passwords, e.g. M@8#Lp2!Qr
"""

import random
import string


def generate_password(length: int = 12,
                       use_upper: bool = True,
                       use_digits: bool = True,
                       use_symbols: bool = True) -> str:
    """
    Build a random password of the given length, guaranteeing at least
    one character from every character-class that's turned on
    (so a 'strong' toggle can't accidentally produce an all-lowercase result).
    """
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase if use_upper else ""
    digits = string.digits if use_digits else ""
    symbols = "!@#$%^&*()-_=+?" if use_symbols else ""

    pool = lower + upper + digits + symbols
    if not pool:
        pool = lower  # safety net, never return an empty password

    # Guarantee at least one char from each enabled class
    required = [random.choice(lower)]
    if use_upper:
        required.append(random.choice(upper))
    if use_digits:
        required.append(random.choice(digits))
    if use_symbols:
        required.append(random.choice(symbols))

    remaining_length = max(length - len(required), 0)
    rest = [random.choice(pool) for _ in range(remaining_length)]

    password_chars = required + rest
    random.shuffle(password_chars)
    return "".join(password_chars)[:max(length, len(required))]
