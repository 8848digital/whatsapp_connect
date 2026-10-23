# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Send one WhatsApp Notification for one document (runs as a background job)."""

import frappe

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_utils import (
	split_lines,
)
from whatsapp_connect.whatsapp_connect_core.messaging.template_params import field_value
from whatsapp_connect.whatsapp_connect_core.messaging.template_send import send_template
from whatsapp_connect.whatsapp_connect_notification.attachments import get_header_media
from whatsapp_connect.whatsapp_connect_notification.doctype.whatsapp_notification.notification_utils import (
	condition_is_true,
)
from whatsapp_connect.whatsapp_connect_notification.recipients import get_recipient_numbers


def send_notification(
	notification: str,
	doctype: str | None = None,
	docname: str | None = None,
	doc_snapshot: dict | None = None,
) -> int:
	"""
	Send the notification's template to all its recipients.

	Parameters:
	        notification (str, required): The WhatsApp Notification name.
	        doctype (str, optional): Doctype of the document.
	        docname (str, optional): Name of the document.
	        doc_snapshot (dict, optional): The document's values, for documents that are deleted.

	Returns:
	        int: The number of messages that Meta accepted.
	"""
	# The notification may have been deleted after the job was queued.
	if not frappe.db.exists("WhatsApp Notification", notification):
		return 0
	settings = frappe.get_doc("WhatsApp Notification", notification)
	if not settings.enabled:
		return 0
	doc = __load_document(doctype, docname, doc_snapshot)
	if not condition_is_true(settings.condition, doc):
		return 0

	numbers = get_recipient_numbers(settings, doc)
	if not numbers:
		return 0
	values = __template_values(settings, doc)
	sent = 0
	for number in numbers:
		message = send_template(
			settings.template,
			number,
			doc=doc,
			values=values,
			account=settings.whatsapp_account,
			source=f"Notification: {settings.name}",
		)
		sent += message.status == "Sent"

	if sent and settings.set_field and doc is not None and not doc_snapshot:
		__set_field(settings, doc)
	return sent


def __load_document(doctype: str | None, docname: str | None, doc_snapshot: dict | None):
	"""
	Load the document, or rebuild it from the snapshot of a deleted document.

	Parameters:
	        doctype (str, optional): Doctype.
	        docname (str, optional): Name.
	        doc_snapshot (dict, optional): Values of a deleted document.

	Returns:
	        Document | None: The document, or None for scheduled notifications without one.
	"""
	if doc_snapshot:
		return frappe.get_doc(doc_snapshot)
	if doctype and docname:
		return frappe.get_doc(doctype, docname)
	return None


def __template_values(settings, doc) -> dict:
	"""
	Values that override the template's own mapping: the notification's fields and header file.

	Parameters:
	        settings (Document, required): The WhatsApp Notification.
	        doc (Document, optional): The document.

	Returns:
	        dict: Template values for send_template.
	"""
	values = get_header_media(settings, doc)
	fields = split_lines(settings.body_fields)
	if fields and doc is not None:
		values["body"] = [field_value(doc, field) or "" for field in fields]
	return values


def __set_field(settings, doc) -> None:
	"""
	Set the configured field on the document after a successful send.

	Parameters:
	        settings (Document, required): The WhatsApp Notification.
	        doc (Document, required): The document.

	Returns:
	        None
	"""
	df = doc.meta.get_field(settings.set_field)
	value = settings.set_value
	if df and df.fieldtype in frappe.model.numeric_fieldtypes:
		value = (
			frappe.utils.flt(value)
			if df.fieldtype in ("Float", "Currency", "Percent")
			else frappe.utils.cint(value)
		)
	frappe.db.set_value(doc.doctype, doc.name, settings.set_field, value)
