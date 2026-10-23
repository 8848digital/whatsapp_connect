# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Scheduled jobs: date-based and scheduled WhatsApp Notifications."""

import json

import frappe
from frappe.utils import add_days, getdate, today

from whatsapp_connect.whatsapp_connect_notification.sending import send_notification

SEND_METHOD = "whatsapp_connect.whatsapp_connect_notification.sending.send_notification"
MAX_DOCUMENTS = 1000


def send_date_based() -> None:
	"""
	Daily: send date-based notifications for documents whose date plus the offset is today.

	Returns:
	        None
	"""
	for notification in frappe.get_all(
		"WhatsApp Notification",
		filters={"enabled": 1, "event_type": "Date Based"},
		fields=["name", "reference_doctype", "date_field", "days_offset"],
	):
		target = getdate(add_days(today(), -(notification.days_offset or 0)))
		names = frappe.get_all(
			notification.reference_doctype,
			filters={notification.date_field: ["between", [target, target]]},
			pluck="name",
			limit=MAX_DOCUMENTS,
		)
		for name in names:
			__queue(notification.name, notification.reference_doctype, name)


def run_scheduled(frequency: str) -> None:
	"""
	Send the scheduled notifications of one frequency.

	With a document type, the notification is sent for each document that
	matches its filters; without one, it is sent once to its numbers and roles.

	Parameters:
	        frequency (str, required): "Hourly", "Daily", "Weekly", "Monthly" or "Yearly".

	Returns:
	        None
	"""
	for notification in frappe.get_all(
		"WhatsApp Notification",
		filters={"enabled": 1, "event_type": "Scheduled", "frequency": frequency},
		fields=["name", "reference_doctype", "document_filters"],
	):
		if not notification.reference_doctype:
			send_notification(notification.name)
			continue
		filters = json.loads(notification.document_filters) if notification.document_filters else {}
		for name in frappe.get_all(
			notification.reference_doctype, filters=filters, pluck="name", limit=MAX_DOCUMENTS
		):
			__queue(notification.name, notification.reference_doctype, name)


def run_hourly() -> None:
	"""
	Hourly scheduler entry.

	Returns:
	        None
	"""
	run_scheduled("Hourly")


def run_daily() -> None:
	"""
	Daily scheduler entry: scheduled and date-based notifications.

	Returns:
	        None
	"""
	run_scheduled("Daily")
	send_date_based()


def run_weekly() -> None:
	"""
	Weekly scheduler entry.

	Returns:
	        None
	"""
	run_scheduled("Weekly")


def run_monthly() -> None:
	"""
	Monthly scheduler entry.

	Returns:
	        None
	"""
	run_scheduled("Monthly")


def run_yearly() -> None:
	"""
	Yearly scheduler entry.

	Returns:
	        None
	"""
	run_scheduled("Yearly")


def __queue(notification: str, doctype: str, name: str) -> None:
	"""
	Send for one document in a background job.

	Parameters:
	        notification (str, required): The WhatsApp Notification name.
	        doctype (str, required): Doctype.
	        name (str, required): Document name.

	Returns:
	        None
	"""
	frappe.enqueue(
		SEND_METHOD,
		queue="long",
		now=bool(frappe.flags.in_test),
		notification=notification,
		doctype=doctype,
		docname=name,
	)
