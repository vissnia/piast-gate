_PESEL_WEIGHTS = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
_NIP_WEIGHTS = (6, 5, 7, 2, 3, 4, 5, 6, 7)
_REGON9_WEIGHTS = (8, 9, 2, 3, 4, 5, 6, 7)
_REGON14_WEIGHTS = (2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8)


def is_valid_pesel(digits: str) -> bool:
    """Validates an 11-digit PESEL: checksum digit plus a plausible
    year/month/day encoded in the first 6 digits."""
    if len(digits) != 11 or not digits.isdigit():
        return False

    checksum = sum(int(d) * w for d, w in zip(digits, _PESEL_WEIGHTS)) % 10
    if (10 - checksum) % 10 != int(digits[10]):
        return False

    month = int(digits[2:4]) % 20
    day = int(digits[4:6])
    return 1 <= month <= 12 and 1 <= day <= 31


def is_valid_nip(digits: str) -> bool:
    """Validates a 10-digit Polish tax identification number (NIP)."""
    if len(digits) != 10 or not digits.isdigit():
        return False

    checksum = sum(int(d) * w for d, w in zip(digits, _NIP_WEIGHTS)) % 11
    return checksum != 10 and checksum == int(digits[9])


def is_valid_regon(digits: str) -> bool:
    """Validates a 9-digit REGON, or a 14-digit REGON (local unit) whose
    first 9 digits are themselves a valid REGON."""
    if not digits.isdigit() or len(digits) not in (9, 14):
        return False

    checksum9 = sum(int(d) * w for d, w in zip(digits, _REGON9_WEIGHTS)) % 11
    if checksum9 == 10:
        checksum9 = 0
    if checksum9 != int(digits[8]):
        return False

    if len(digits) == 9:
        return True

    checksum14 = sum(int(d) * w for d, w in zip(digits, _REGON14_WEIGHTS)) % 11
    if checksum14 == 10:
        checksum14 = 0
    return checksum14 == int(digits[13])


def is_valid_iban_checksum(code: str) -> bool:
    """ISO 7064 MOD 97-10 check used by IBAN, and by Polish NRB once
    prefixed with the "PL" country code (a Polish NRB is, by construction,
    an IBAN's BBAN plus the same two check digits)."""
    if len(code) < 4 or not code[:2].isalpha() or not code[2:4].isdigit():
        return False

    rearranged = code[4:] + code[:4]
    try:
        numeric = "".join(str(int(c, 36)) for c in rearranged.upper())
    except ValueError:
        return False

    return int(numeric) % 97 == 1
