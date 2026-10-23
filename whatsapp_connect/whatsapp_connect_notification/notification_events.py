# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""doc_events for all doctypes: queue the WhatsApp Notifications that match an event."""

import frappe

from whatsapp_connect.whatsapp_connect_notification.doctype.whatsapp_notification.notification_utils import (
	get_notification_map,
)

EVENTS = {
	"after_insert": ("New",),
	"on_update": ("Save", "Value Change"),
	"on_submit": ("Submit",),
	"on_cancel": ("Cancel",),
	"on_trash": ("Delete",),
	"on_update_after_submit": ("Save After Submit", "Value Change"),
}
SEND_METHOD = "whatsapp_connect.whatsapp_connect_notification.sending.send_notification"


def handle_event(doc, method: str) -> None:
	"""
	Queue the notifications for this doctype and event (doc_events "*" hook).

	Nothing is sent during install, migrate, data import or patches.

	Parameters:
	        doc (Document, required): The document of the event.
	        method (str, required): The hook name, for example "on_submit".

	Returns:
	        None
	"""
	if (
		frappe.flags.in_install
		or frappe.flags.in_migrate
		or frappe.flags.in_import
		or frappe.flags.in_patch
	):
		return
	by_event = get_notification_map().get(doc.doctype)
	if not by_event:
		return
	for event in EVENTS.get(method, ()):
		for notification in by_event.get(event, []):
			if event == "Value Change" and not __value_changed(notification, doc):
				continue
			queue_notification(notification, doc, snapshot=method == "on_trash")


def queue_notification(notification: str, doc, snapshot: bool = False) -> None:
	"""
	Send the notification in a background job after the transaction commits.

	Parameters:
	        notification (str, required): The WhatsApp Notification name.
	        doc (Document, required): The document.
	        snapshot (bool, optional): Pass the document's values, for a document being deleted.

	Returns:
	        None
	"""
	frappe.enqueue(
		SEND_METHOD,
		queue="short",
		enqueue_after_commit=True,
		now=bool(frappe.flags.in_test),
		notification=notification,
		doctype=doc.doctype,
		docname=doc.name,
		doc_snapshot=doc.as_dict(convert_dates_to_str=True) if snapshot else None,
	)


def __value_changed(notification: str, doc) -> bool:
	"""
	Tell if the notification's watched field changed in this save.

	Parameters:
	        notification (str, required): The WhatsApp Notification name.
	        doc (Document, required): The saved document.

	Returns:
	        bool: True when the field's value changed.
	"""
	fieldname = frappe.db.get_value("WhatsApp Notification", notification, "value_changed")
	return bool(fieldname) and doc.has_value_changed(fieldname)
