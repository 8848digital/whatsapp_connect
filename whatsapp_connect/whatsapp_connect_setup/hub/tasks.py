# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Scheduled clean-up on the hub."""

import frappe
from frappe.utils import add_days, now_datetime

DOCTYPE = "WhatsApp Hub Connection"


def delete_stale_sessions() -> None:
	"""
	Delete signup sessions that were never claimed, one day after they started.

	Returns:
	        None
	"""
	if not frappe.db.get_single_value("WhatsApp Hub Settings", "enabled"):
		return
	filters = {
		"status": ["in", ["Pending", "Connected"]],
		"creation": ["<", add_days(now_datetime(), -1)],
	}
	for name in frappe.get_all(DOCTYPE, filters=filters, pluck="name"):
		frappe.delete_doc(DOCTYPE, name, ignore_permissions=True, force=True)
