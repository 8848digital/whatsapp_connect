# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Scheduled jobs of the campaign module."""

import frappe
from frappe.utils import now_datetime

from whatsapp_connect.whatsapp_connect_campaign.campaign_sender import finish_if_done
from whatsapp_connect.whatsapp_connect_campaign.doctype.whatsapp_campaign.campaign_utils import (
	start_campaign,
)


def start_due_campaigns() -> None:
	"""
	Start the scheduled campaigns whose send time has come (scheduler "all", every few minutes).

	Each campaign is marked Sending and committed before its jobs are queued, so
	a later error cannot put it back to Scheduled and send it twice.

	Returns:
	        None
	"""
	due = frappe.get_all(
		"WhatsApp Campaign",
		filters={"docstatus": 1, "status": "Scheduled", "scheduled_at": ["<=", now_datetime()]},
		pluck="name",
	)
	for name in due:
		frappe.db.set_value("WhatsApp Campaign", name, "status", "Sending")
		if not frappe.flags.in_test:
			frappe.db.commit()  # nosemgrep: frappe-manual-commit -- claim the campaign before its jobs are queued
		try:
			start_campaign(name)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"WhatsApp Campaign could not start: {name}")


def refresh_running_campaigns() -> None:
	"""
	Hourly: update the counts of campaigns that are sending, and close finished ones.

	Delivered and read counts change later, as Meta reports the statuses.

	Returns:
	        None
	"""
	for name in frappe.get_all(
		"WhatsApp Campaign", filters={"docstatus": 1, "status": "Sending"}, pluck="name"
	):
		finish_if_done(name)
