# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""WhatsApp messages as cards in the timeline of the document they belong to."""

import frappe
from frappe import _
from frappe.utils import escape_html, strip_html_tags

from whatsapp_connect.whatsapp_connect_core.messaging.contact_link import get_linked_contacts

TIMELINE_LIMIT = 50
PREVIEW_LENGTH = 300
FIELDS = ["name", "direction", "phone_number", "status", "message_type", "body", "creation"]


def get_timeline_content(doctype: str, docname: str) -> list[dict]:
	"""
	Timeline cards for the WhatsApp Messages of a document (additional_timeline_content hook).

	A Customer, Supplier or Lead also shows the messages of its linked contacts.

	Parameters:
	        doctype (str, required): Doctype of the open form.
	        docname (str, required): Name of the open document.

	Returns:
	        list[dict]: Timeline items; empty when the user cannot read WhatsApp Message.
	"""
	if doctype == "WhatsApp Message" or not frappe.has_permission("WhatsApp Message", "read"):
		return []

	messages = __messages({"reference_doctype": doctype, "reference_name": docname})
	contacts = get_linked_contacts(doctype, docname)
	if contacts:
		messages += __messages({"reference_doctype": "Contact", "reference_name": ["in", contacts]})
		messages = sorted(messages, key=lambda message: message.creation, reverse=True)[:TIMELINE_LIMIT]

	return [__card(message) for message in messages]


def __messages(filters: dict) -> list:
	"""
	Load the latest messages for the given filters.

	Parameters:
	        filters (dict, required): Filters on WhatsApp Message.

	Returns:
	        list: Message rows, newest first.
	"""
	return frappe.get_all(
		"WhatsApp Message",
		filters=filters,
		fields=FIELDS,
		order_by="creation desc",
		limit=TIMELINE_LIMIT,
	)


def __card(message) -> dict:
	"""
	Build one timeline card.

	Parameters:
	        message (dict, required): A WhatsApp Message row.

	Returns:
	        dict: Timeline item with icon, card flag, time and HTML content.
	"""
	number = escape_html(message.phone_number or "")
	incoming = message.direction == "Incoming"
	title = _("WhatsApp from {0}").format(number) if incoming else _("WhatsApp to {0}").format(number)
	link = frappe.utils.get_link_to_form("WhatsApp Message", message.name, title)

	text = strip_html_tags(message.body or "").strip()
	if len(text) > PREVIEW_LENGTH:
		text = text[:PREVIEW_LENGTH] + "…"
	body = escape_html(text) or escape_html(_(message.message_type or ""))

	reply = ""
	if incoming:
		# Opens the Send WhatsApp dialog (public/js/whatsapp_connect.js).
		reply = f' · <a href="#" class="whatsapp-connect-reply" data-number="{number}">{_("Reply")}</a>'

	status = escape_html(_(message.status or ""))
	return {
		"icon": "small-message",
		"is_card": True,
		"creation": message.creation,
		"content": (
			f"<div>{link} · <span class='text-muted'>{status}</span>{reply}</div>"
			f"<div class='text-muted small'>{body}</div>"
		),
	}
