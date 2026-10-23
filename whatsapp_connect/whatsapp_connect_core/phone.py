# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Phone number helpers. WhatsApp identifies people by digits-only numbers with a country code."""

import re

import frappe

MIN_DIGITS = 8
MAX_DIGITS = 15
MATCH_DIGITS = 10


def normalize_number(number: str | None, default_country_code: str | None = None) -> str | None:
	"""
	Reduce a typed phone number to the digits-only international form Meta uses.

	A number written with "+" or "00" is taken as international. Otherwise, if
	a default country code is set (WhatsApp Settings), a national number such
	as "09900000101" becomes "919900000101".

	Parameters:
	        number (str, optional): The number as typed, for example "+91 99000 00101".
	        default_country_code (str, optional): Country code for national numbers;
	                defaults to WhatsApp Settings.

	Returns:
	        str | None: Digits only, or None if the result is not a usable number.
	"""
	raw = (number or "").strip()
	digits = re.sub(r"\D", "", raw)
	if not digits:
		return None

	if raw.startswith("00"):
		digits = digits[2:]
	elif not raw.startswith("+"):
		digits = __add_country_code(digits, default_country_code)

	if not MIN_DIGITS <= len(digits) <= MAX_DIGITS:
		return None
	return digits


def number_suffix(number: str | None) -> str | None:
	"""
	Return the last digits of a number, used to match numbers stored in any format.

	Parameters:
	        number (str, optional): A phone number in any format.

	Returns:
	        str | None: The last 10 digits, or None when the number has fewer than 7 digits.
	"""
	digits = re.sub(r"\D", "", number or "")
	if len(digits) < 7:
		return None
	return digits[-MATCH_DIGITS:]


def __add_country_code(digits: str, default_country_code: str | None) -> str:
	"""
	Prefix the default country code to a national number.

	Parameters:
	        digits (str, required): Digits of a number typed without "+" or "00".
	        default_country_code (str, optional): Code to add; read from WhatsApp Settings when None.

	Returns:
	        str: The number with the country code, or unchanged when it already looks international.
	"""
	country_code = default_country_code
	if country_code is None:
		country_code = frappe.db.get_single_value("WhatsApp Settings", "default_country_code")
	country_code = re.sub(r"\D", "", country_code or "")
	if not country_code:
		return digits

	if digits.startswith("0"):
		return country_code + digits.lstrip("0")
	if len(digits) <= 10:
		return country_code + digits
	return digits
