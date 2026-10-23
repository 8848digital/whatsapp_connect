# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Server side of the Send WhatsApp dialog: the numbers of a document, templates and replies."""

import re

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.messaging.contact_link import get_linked_contacts
from whatsapp_connect.whatsapp_connect_core.messaging.reply_window import is_window_open
from whatsapp_connect.whatsapp_connect_core.messaging.template_send import send_template
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number

PHONE_FIELD_PATTERN = re.compile(r"mobile|phone|whatsapp|cell")


def get_send_options(doctype: str, name: str) -> list[dict]:
	"""
	Return the numbers of a document and of its contacts, each with its reply window state.

	Parameters:
	        doctype (str, required): Doctype of the open form.
	        name (str, required): Name of the document.

	Returns:
	        list[dict]: {"number", "label", "window_open"} without duplicates.
	"""
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	numbers = {}
	for label, number in __document_numbers(doc):
		numbers.setdefault(number, label)
	return [
		{"number": number, "label": f"{number} · {label}", "window_open": is_window_open(number)}
		for number, label in numbers.items()
	]


def send_template_to(template: str, to: str, doctype: str, name: str):
	"""
	Send an approved template to a number, with the variables filled from the document.

	Parameters:
	        template (str, required): The WhatsApp Template name.
	        to (str, required): The recipient's number.
	        doctype (str, required): Doctype of the document.
	        name (str, required): Name of the document.

	Returns:
	        Document: The WhatsApp Message.
	"""
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	frappe.has_permission("WhatsApp Message", "create", throw=True)
	return send_template(template, to, doc=doc, source=_("Sent by {0}").format(frappe.session.user))


def send_reply(to: str, text: str, doctype: str | None = None, name: str | None = None):
	"""
	Send free text to a customer who wrote in the last 24 hours.

	Parameters:
	        to (str, required): The customer's number.
	        text (str, required): The reply text.
	        doctype (str, optional): Doctype of the document the reply belongs to.
	        name (str, optional): Name of that document.

	Returns:
	        Document: The WhatsApp Message.
	"""
	if not (text or "").strip():
		frappe.throw(_("Enter the reply text"))
	if not is_window_open(to):
		frappe.throw(
			_("The customer has not written in the last 24 hours. WhatsApp allows only templates now."),
			title=_("Reply window closed"),
		)
	if doctype and name:
		frappe.get_doc(doctype, name).check_permission("read")
	message = frappe.get_doc(
		{
			"doctype": "WhatsApp Message",
			"direction": "Outgoing",
			"message_type": "text",
			"body": text,
			"phone_number": to,
			"reference_doctype": doctype,
			"reference_name": name,
			"source": _("Sent by {0}").format(frappe.session.user),
		}
	)
	message.insert()
	message.reload()
	return message


def __document_numbers(doc):
	"""
	Yield (label, number) for the document's phone fields and its contacts' numbers.

	Parameters:
	        doc (Document, required): The document.

	Returns:
	        Iterator[tuple[str, str]]: Labels and digits-only numbers.
	"""
	for df in doc.meta.fields:
		if df.fieldtype in ("Data", "Phone") and (
			df.fieldtype == "Phone" or df.options == "Phone" or PHONE_FIELD_PATTERN.search(df.fieldname)
		):
			number = normalize_number(doc.get(df.fieldname))
			if number:
				yield _(df.label or df.fieldname), number

	contacts = [doc.name] if doc.doctype == "Contact" else get_linked_contacts(doc.doctype, doc.name)
	for contact in contacts:
		for phone in frappe.get_all(
			"Contact Phone", filters={"parent": contact, "parenttype": "Contact"}, pluck="phone"
		):
			number = normalize_number(phone)
			if number:
				yield contact, number
