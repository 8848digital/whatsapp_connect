# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Send from the Frappe CRM WhatsApp tab through WhatsApp Connect."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.messaging.reply_window import is_window_open
from whatsapp_connect.whatsapp_connect_core.messaging.template_send import send_template
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number

MEDIA_TYPES = ("image", "video", "audio", "document")


def send_message(
	doc, to: str, text: str | None, attach: str | None, reply_to: str | None, content_type: str
):
	"""
	Send text or a file from a CRM record, as a reply to a message when reply_to is set.

	Parameters:
	        doc (Document, required): The CRM Lead or CRM Deal.
	        to (str, required): The customer's number.
	        text (str, optional): The text, or the caption of a file.
	        attach (str, optional): URL of the file to send.
	        reply_to (str, optional): The WhatsApp Message being answered.
	        content_type (str, required): "text", "image", "video", "audio" or "document".

	Returns:
	        Document: The WhatsApp Message.
	"""
	number = __number(to)
	if not is_window_open(number):
		frappe.throw(
			_("The customer has not written in the last 24 hours. WhatsApp allows only templates now."),
			title=_("Reply window closed"),
		)
	media = content_type in MEDIA_TYPES and attach
	values = {
		"message_type": content_type if media else "text",
		"body": None if media and text == attach else text,
		"attachment": attach if media else None,
	}
	if reply_to:
		values["reply_to_wamid"] = frappe.db.get_value("WhatsApp Message", reply_to, "wamid")
	return __insert(doc, number, values)


def send_reaction(emoji: str, reply_to_name: str):
	"""
	React with an emoji to a message, in the same conversation.

	Parameters:
	        emoji (str, required): The emoji.
	        reply_to_name (str, required): The WhatsApp Message to react to.

	Returns:
	        Document: The reaction WhatsApp Message.
	"""
	target = frappe.get_doc("WhatsApp Message", reply_to_name)
	doc = None
	if target.reference_doctype and target.reference_name:
		doc = frappe.get_doc(target.reference_doctype, target.reference_name)
	values = {"message_type": "reaction", "reaction_emoji": emoji, "reply_to_wamid": target.wamid}
	return __insert(doc, target.phone_number, values)


def send_crm_template(doc, template: str, to: str):
	"""
	Send an approved template with its variables filled from the CRM record.

	Parameters:
	        doc (Document, required): The CRM Lead or CRM Deal.
	        template (str, required): The WhatsApp Template name.
	        to (str, required): The customer's number.

	Returns:
	        Document: The WhatsApp Message.
	"""
	return send_template(template, __number(to), doc=doc, source=__source())


def __insert(doc, number: str, values: dict):
	"""
	Insert (and so send) an outgoing message linked to the CRM record.

	Parameters:
	        doc (Document, optional): The CRM record.
	        number (str, required): Digits-only number.
	        values (dict, required): Content fields.

	Returns:
	        Document: The WhatsApp Message.
	"""
	message = frappe.get_doc(
		{
			"doctype": "WhatsApp Message",
			"direction": "Outgoing",
			"phone_number": number,
			# The account the customer wrote to; the default outgoing account when empty.
			"whatsapp_account": frappe.db.get_value("WhatsApp Profile", number, "whatsapp_account"),
			"reference_doctype": doc.doctype if doc else None,
			"reference_name": doc.name if doc else None,
			"source": __source(),
			**values,
		}
	)
	message.insert(ignore_permissions=True)
	return message


def __number(to: str) -> str:
	"""
	Return the digits-only number, or stop when it is not valid.

	Parameters:
	        to (str, required): A number in any format.

	Returns:
	        str: Digits only.
	"""
	number = normalize_number(to)
	if not number:
		frappe.throw(_("{0} is not a valid phone number").format(to))
	return number


def __source() -> str:
	"""
	Return the source text of messages sent from Frappe CRM.

	Returns:
	        str: "Sent by <user> from CRM".
	"""
	return _("Sent by {0} from CRM").format(frappe.session.user)
