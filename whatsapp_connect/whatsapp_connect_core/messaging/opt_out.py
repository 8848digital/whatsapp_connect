# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Opt-out: customers who send STOP get no templates or campaigns until they send START."""

import frappe
from frappe.utils import now_datetime

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_profile.profile_utils import (
	get_or_create_profile,
)
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number

OPT_OUT_KEYWORDS = {"stop", "stop all", "unsubscribe", "opt out", "optout"}
OPT_IN_KEYWORDS = {"start", "unstop", "subscribe", "opt in", "optin"}


def apply_keyword(number: str, text: str | None, account: str | None = None) -> str | None:
	"""
	Opt the number out or in when the whole message is an opt-out or opt-in keyword.

	Only the whole message counts, so "please stop the order" changes nothing.

	Parameters:
	        number (str, required): Digits-only phone number of the sender.
	        text (str, optional): The message text.
	        account (str, optional): The receiving WhatsApp Account.

	Returns:
	        str | None: "opted_out", "opted_in" or None when the text is not a keyword.
	"""
	keyword = (text or "").strip().lower().rstrip(".!")
	if keyword in OPT_OUT_KEYWORDS:
		set_opted_out(number, True, account)
		return "opted_out"
	if keyword in OPT_IN_KEYWORDS:
		set_opted_out(number, False, account)
		return "opted_in"
	return None


def set_opted_out(number: str, opted_out: bool, account: str | None = None) -> None:
	"""
	Set or clear the opt-out flag on the number's WhatsApp Profile.

	Parameters:
	        number (str, required): Digits-only phone number.
	        opted_out (bool, required): True to opt out, False to opt in.
	        account (str, optional): WhatsApp Account, used when the profile is created.

	Returns:
	        None
	"""
	profile = get_or_create_profile(number, account=account)
	frappe.db.set_value(
		"WhatsApp Profile",
		profile,
		{
			"opted_out": int(opted_out),
			"opted_out_on": now_datetime() if opted_out else None,
		},
	)


def is_opted_out(number: str | None) -> bool:
	"""
	Tell if a number has opted out.

	Parameters:
	        number (str, optional): A phone number in any format.

	Returns:
	        bool: True when the number's profile is opted out.
	"""
	normalized = normalize_number(number)
	if not normalized:
		return False
	return bool(frappe.db.get_value("WhatsApp Profile", {"name": normalized, "opted_out": 1}))


def filter_opted_out(numbers: list[str]) -> tuple[list[str], list[str]]:
	"""
	Split numbers into the ones that may receive templates and the opted-out ones.

	Parameters:
	        numbers (list[str], required): Phone numbers in any format.

	Returns:
	        tuple[list[str], list[str]]: (allowed numbers, opted-out numbers), in the input order.
	"""
	normalized = {number: normalize_number(number) for number in numbers}
	opted_out = set(
		frappe.get_all(
			"WhatsApp Profile",
			filters={"name": ["in", [n for n in normalized.values() if n] or [""]], "opted_out": 1},
			pluck="name",
		)
	)
	allowed = [number for number in numbers if normalized[number] not in opted_out]
	skipped = [number for number in numbers if normalized[number] in opted_out]
	return allowed, skipped
