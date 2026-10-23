# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Business logic for WhatsApp Notification: validation, the event map and conditions."""

import json

import frappe
from frappe import _
from frappe.utils.safe_exec import get_safe_globals

MAP_CACHE_KEY = "whatsapp_connect:notification_map"
FIELD_SETTINGS = ("phone_field", "value_changed", "date_field", "attach_from_field", "set_field")


def validate_notification(notification) -> None:
	"""
	Check that the notification can work before it is saved.

	Parameters:
	        notification (Document, required): The WhatsApp Notification being saved.

	Returns:
	        None
	"""
	__validate_fields(notification)
	if notification.event_type == "Document Event" and not has_recipients(notification):
		frappe.throw(
			_("Choose who receives the message: a phone field, the party, other numbers or roles")
		)
	if (
		notification.event_type == "Scheduled"
		and not notification.reference_doctype
		and not (notification.fixed_numbers or notification.recipient_roles)
	):
		frappe.throw(_("A scheduled notification without a document type needs other numbers or roles"))
	if notification.document_event == "Value Change" and not notification.value_changed:
		frappe.throw(_("Select the field that changes"))
	if notification.document_event == "Delete" and notification.set_field:
		frappe.throw(_("A field cannot be set on a deleted document"))
	if notification.print_format:
		print_doctype = frappe.db.get_value("Print Format", notification.print_format, "doc_type")
		if print_doctype != notification.reference_doctype:
			frappe.throw(
				_("Print Format {0} is not for {1}").format(
					notification.print_format, notification.reference_doctype
				)
			)
	if notification.document_filters:
		try:
			json.loads(notification.document_filters)
		except ValueError:
			frappe.throw(_("Document Filters must be valid JSON"))


def has_recipients(notification) -> bool:
	"""
	Tell if any recipient source is set.

	Parameters:
	        notification (Document, required): The WhatsApp Notification.

	Returns:
	        bool: True when a phone field, the party, numbers or roles are set.
	"""
	return bool(
		notification.phone_field
		or notification.send_to_party
		or notification.fixed_numbers
		or notification.recipient_roles
	)


def get_notification_map() -> dict:
	"""
	Return the enabled Document Event notifications by doctype and event (cached).

	Returns:
	        dict: {doctype: {event: [notification names]}}
	"""
	cached = frappe.cache().get_value(MAP_CACHE_KEY)
	if cached is not None:
		return cached
	notification_map = {}
	for row in frappe.get_all(
		"WhatsApp Notification",
		filters={"enabled": 1, "event_type": "Document Event"},
		fields=["name", "reference_doctype", "document_event"],
	):
		notification_map.setdefault(row.reference_doctype, {}).setdefault(row.document_event, []).append(
			row.name
		)
	frappe.cache().set_value(MAP_CACHE_KEY, notification_map)
	return notification_map


def clear_notification_map() -> None:
	"""
	Drop the cached event map, so a saved or deleted notification applies at once.

	Returns:
	        None
	"""
	frappe.cache().delete_value(MAP_CACHE_KEY)


def condition_is_true(condition: str | None, doc) -> bool:
	"""
	Evaluate a notification or role condition in Frappe's safe evaluator.

	Parameters:
	        condition (str, optional): A Python expression using "doc".
	        doc (Document, optional): The document; None for scheduled notifications without one.

	Returns:
	        bool: True when there is no condition or it evaluates to true.
	"""
	if not condition:
		return True
	context = {"doc": doc.as_dict() if hasattr(doc, "as_dict") else doc}
	return bool(frappe.safe_eval(condition, get_safe_globals(), context))


def __validate_fields(notification) -> None:
	"""
	Check that the selected fields exist on the document type.

	Parameters:
	        notification (Document, required): The WhatsApp Notification.

	Returns:
	        None
	"""
	if not notification.reference_doctype:
		return
	meta = frappe.get_meta(notification.reference_doctype)
	for setting in FIELD_SETTINGS:
		fieldname = notification.get(setting)
		if (
			fieldname
			and not meta.has_field(fieldname)
			and fieldname not in ("name", "creation", "modified")
		):
			frappe.throw(_("{0} has no field {1}").format(notification.reference_doctype, fieldname))
