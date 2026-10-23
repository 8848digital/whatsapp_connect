# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Scheduled jobs of the core module."""

import frappe
from frappe.utils import add_days, now_datetime

DEFAULT_RETENTION_DAYS = 30


def clear_old_logs() -> None:
	"""
	Delete WhatsApp Logs older than the retention set in WhatsApp Settings (daily job).

	Returns:
	        None
	"""
	days = frappe.db.get_single_value("WhatsApp Settings", "log_retention_days")
	days = DEFAULT_RETENTION_DAYS if days is None else days
	if days <= 0:
		return
	frappe.db.delete("WhatsApp Log", {"creation": ["<", add_days(now_datetime(), -days)]})
