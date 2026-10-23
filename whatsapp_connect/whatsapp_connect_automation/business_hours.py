# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Business hours of WhatsApp Auto Reply Settings."""

import frappe
from frappe.utils import get_time, now_datetime

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def is_open(moment=None) -> bool:
	"""
	Tell if the business is open, in the system time zone.

	A day without a row is closed. Without any rows, the business is always open,
	so away messages are not sent before the hours are set.

	Parameters:
	        moment (datetime, optional): The time to check; now when empty.

	Returns:
	        bool: True during business hours.
	"""
	rows = frappe.get_all(
		"WhatsApp Business Hour",
		filters={"parent": "WhatsApp Auto Reply Settings", "parenttype": "WhatsApp Auto Reply Settings"},
		fields=["day", "opens_at", "closes_at"],
	)
	if not rows:
		return True
	moment = moment or now_datetime()
	day = DAYS[moment.weekday()]
	time = moment.time()
	return any(
		get_time(row.opens_at) <= time < get_time(row.closes_at) for row in rows if row.day == day
	)
