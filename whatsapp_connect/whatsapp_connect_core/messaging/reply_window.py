# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""The 24-hour customer service window: free text is allowed only after the customer writes."""

import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime

from whatsapp_connect.whatsapp_connect_core.phone import normalize_number

WINDOW_HOURS = 24


def is_window_open(number: str | None) -> bool:
	"""
	Tell if the customer wrote in the last 24 hours.

	Parameters:
	        number (str, optional): The customer's phone number in any format.

	Returns:
	        bool: True when a free-text message may be sent.
	"""
	normalized = normalize_number(number)
	if not normalized:
		return False
	last_incoming = frappe.db.get_value("WhatsApp Profile", normalized, "last_incoming_at")
	if not last_incoming:
		return False
	return get_datetime(last_incoming) >= add_to_date(now_datetime(), hours=-WINDOW_HOURS)
