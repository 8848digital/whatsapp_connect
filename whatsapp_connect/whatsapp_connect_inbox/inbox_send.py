# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Send text, files and templates from the WhatsApp Inbox."""

import mimetypes

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.messaging.media import get_local_file
from whatsapp_connect.whatsapp_connect_core.messaging.reply_window import is_window_open
from whatsapp_connect.whatsapp_connect_core.messaging.template_params import get_template_params
from whatsapp_connect.whatsapp_connect_core.messaging.template_send import send_template
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number
from whatsapp_connect.whatsapp_connect_inbox.conversations import check_access, get_profile_name
from whatsapp_connect.whatsapp_connect_inbox.message_view import get_reference

# Media types that WhatsApp shows inline; any other file goes as a document.
INLINE_MIME_TYPES = {
	"image/jpeg": "image",
	"image/png": "image",
	"video/mp4": "video",
	"video/3gpp": "video",
	"audio/aac": "audio",
	"audio/amr": "audio",
	"audio/mpeg": "audio",
	"audio/mp4": "audio",
	"audio/ogg": "audio",
}


def send_text(phone_number: str, text: str, reply_to: str | None = None):
	"""
	Send free text in a conversation, optionally as a reply to one of its messages.

	Parameters:
	        phone_number (str, required): The customer's number.
	        text (str, required): The message text.
	        reply_to (str, optional): The WhatsApp Message being answered.

	Returns:
	        Document: The WhatsApp Message.
	"""
	if not (text or "").strip():
		frappe.throw(_("Enter the message text"))
	return __send(phone_number, {"message_type": "text", "body": text}, reply_to)


def send_file(phone_number: str, file_url: str, caption: str | None = None):
	"""
	Send an uploaded file as an image, video, audio or document message.

	The file is attached to the message, so other agents can open it too.

	Parameters:
	        phone_number (str, required): The customer's number.
	        file_url (str, required): URL of a file uploaded to this site.
	        caption (str, optional): Text shown under images, videos and documents.

	Returns:
	        Document: The WhatsApp Message.
	"""
	file_doc = get_local_file(file_url)
	if not file_doc or not file_doc.has_permission("read"):
		frappe.throw(_("Upload the file first"))
	mime_type = mimetypes.guess_type(file_doc.file_name or "")[0] or ""
	values = {
		"message_type": INLINE_MIME_TYPES.get(mime_type, "document"),
		"attachment": file_doc.file_url,
		"filename": file_doc.file_name,
		"mime_type": mime_type,
		"body": caption,
	}
	message = __send(phone_number, values)
	if not file_doc.attached_to_doctype:
		file_doc.db_set({"attached_to_doctype": "WhatsApp Message", "attached_to_name": message.name})
	return message


def send_template_message(phone_number: str, template: str, body_values: list | None = None):
	"""
	Send an approved template. This also starts a conversation with a new number.

	The variables come from the values typed by the agent, else from the record
	the conversation belongs to, else from the template's samples.

	Parameters:
	        phone_number (str, required): The customer's number in any format.
	        template (str, required): The WhatsApp Template name.
	        body_values (list, optional): Values for {{1}}, {{2}}... of the body.

	Returns:
	        Document: The WhatsApp Message.
	"""
	check_access("create")
	number = normalize_number(phone_number)
	if not number:
		frappe.throw(_("{0} is not a valid phone number").format(phone_number))
	template_doc = frappe.get_doc("WhatsApp Template", template)
	template_doc.check_permission("read")

	doc = __reference_doc(number) if frappe.db.exists("WhatsApp Profile", number) else None
	values = None
	if body_values and any(body_values):
		# A variable left empty keeps the value from the record or the sample.
		defaults = get_template_params(template_doc, doc)["body"]
		given = list(body_values) + [""] * len(defaults)
		values = {"body": [given[index] or default for index, default in enumerate(defaults)]}
	message = send_template(template, number, doc=doc, values=values, source=__source())
	if not frappe.db.get_value("WhatsApp Profile", number, "conversation_status"):
		frappe.db.set_value("WhatsApp Profile", number, "conversation_status", "Open")
	return message


def __send(phone_number: str, values: dict, reply_to: str | None = None):
	"""
	Create and send a session message in a conversation whose reply window is open.

	Parameters:
	        phone_number (str, required): The customer's number.
	        values (dict, required): WhatsApp Message fields of the content.
	        reply_to (str, optional): The WhatsApp Message being answered.

	Returns:
	        Document: The WhatsApp Message.
	"""
	check_access("create")
	number = get_profile_name(phone_number)
	if not is_window_open(number):
		frappe.throw(
			_("The customer has not written in the last 24 hours. WhatsApp allows only templates now."),
			title=_("Reply window closed"),
		)
	reference = get_reference(number) or {}
	message = frappe.get_doc(
		{
			"doctype": "WhatsApp Message",
			"direction": "Outgoing",
			"phone_number": number,
			"whatsapp_account": frappe.db.get_value("WhatsApp Profile", number, "whatsapp_account"),
			"reply_to_wamid": __reply_wamid(reply_to, number),
			"reference_doctype": reference.get("doctype"),
			"reference_name": reference.get("name"),
			"source": __source(),
			**values,
		}
	)
	message.insert()
	message.reload()
	return message


def __reference_doc(number: str):
	"""
	Return the record the conversation belongs to, when the user can read it.

	Parameters:
	        number (str, required): The WhatsApp Profile name.

	Returns:
	        Document | None: The reference document.
	"""
	reference = get_reference(number)
	if not reference or not frappe.db.exists(reference["doctype"], reference["name"]):
		return None
	doc = frappe.get_doc(reference["doctype"], reference["name"])
	return doc if doc.has_permission("read") else None


def __reply_wamid(reply_to: str | None, number: str) -> str | None:
	"""
	Return Meta's ID of the message being answered, which must be in the same conversation.

	Parameters:
	        reply_to (str, optional): The WhatsApp Message name.
	        number (str, required): The conversation's number.

	Returns:
	        str | None: The wamid, or None when there is no reply.
	"""
	if not reply_to:
		return None
	row = frappe.db.get_value("WhatsApp Message", reply_to, ["phone_number", "wamid"], as_dict=True)
	if not row or row.phone_number != number:
		frappe.throw(_("The message you answer is not in this conversation"))
	return row.wamid


def __source() -> str:
	"""
	Return the source text of messages sent by the current user.

	Returns:
	        str: "Sent by <user>".
	"""
	return _("Sent by {0}").format(frappe.session.user)
