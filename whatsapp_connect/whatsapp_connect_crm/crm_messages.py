# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""WhatsApp Messages in the shape of the Frappe CRM WhatsApp tab (frappe_whatsapp field names)."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_crm.crm_access import get_numbers
from whatsapp_connect.whatsapp_connect_inbox.message_view import get_message_rows

LIMIT = 200
STATUSES = {
	"Sent": "sent",
	"Queued": "sent",
	"Delivered": "delivered",
	"Read": "read",
	"Failed": "failed",
	"Opted Out": "failed",
}
CONTENT_TYPES = {
	"image": "image",
	"sticker": "image",
	"video": "video",
	"audio": "audio",
	"document": "document",
	"button": "button",
	"reaction": "reaction",
}


def get_messages(doc) -> list[dict]:
	"""
	Return the messages of a record's numbers, oldest first, as the CRM tab shows them.

	Messages are found by number, so a message linked to the record's Contact shows too.
	Reactions are added to the message they react to.

	Parameters:
	        doc (Document, required): A CRM Lead or CRM Deal.

	Returns:
	        list[dict]: Messages with frappe_whatsapp field names.
	"""
	rows = []
	for number in get_numbers(doc):
		rows += get_message_rows(number, None, LIMIT)
	rows.sort(key=lambda row: row.creation)
	names = __profile_names([row.get("phone_number") for row in rows])
	messages = [__crm_row(row, doc, names) for row in rows]
	by_wamid = {message["message_id"]: message for message in messages if message["message_id"]}
	for message in messages:
		target = by_wamid.get(message["reply_to_message_id"])
		if message["content_type"] == "reaction" and target:
			target["reaction"] = message["message"]
		elif message["is_reply"] and target:
			message.update(
				{
					"reply_message": target["template"] or target["message"],
					"reply_to": target["name"],
					"reply_to_type": target["type"],
					"reply_to_from": target["from_name"],
				}
			)
	return [message for message in messages if message["content_type"] != "reaction"]


def __crm_row(row: dict, doc, names: dict) -> dict:
	"""
	Rename the fields of one message for the CRM tab.

	Parameters:
	        row (dict, required): A message from get_message_rows.
	        doc (Document, required): The CRM record.
	        names (dict, required): WhatsApp names by number.

	Returns:
	        dict: The message with frappe_whatsapp field names.
	"""
	incoming = row.direction == "Incoming"
	template = row.message_type == "template"
	return {
		"name": row.name,
		"type": row.direction,
		"from": row.phone_number if incoming else None,
		"to": None if incoming else row.phone_number,
		"from_name": (names.get(row.phone_number) or row.phone_number) if incoming else _("You"),
		"content_type": CONTENT_TYPES.get(row.message_type, "text"),
		"message_type": "Template" if template else "Manual",
		"message": row.reaction_emoji if row.message_type == "reaction" else (row.body or ""),
		"attach": row.attachment,
		"template": row.get("template_text") if template else None,
		"template_name": row.template,
		"header": row.get("template_header") or "",
		"footer": row.get("template_footer") or "",
		"status": STATUSES.get(row.status, ""),
		"message_id": row.wamid,
		"is_reply": bool(row.reply_to_wamid) and row.message_type != "reaction",
		"reply_to_message_id": row.reply_to_wamid,
		"reference_doctype": doc.doctype,
		"reference_name": doc.name,
		"creation": row.creation,
	}


def __profile_names(numbers: list) -> dict:
	"""
	Return the WhatsApp name of each number.

	Parameters:
	        numbers (list, required): Profile names (numbers).

	Returns:
	        dict: {number: WhatsApp name}.
	"""
	rows = frappe.get_all(
		"WhatsApp Profile",
		filters={"name": ["in", list(set(numbers)) or [""]]},
		fields=["name", "profile_name"],
	)
	return {row.name: row.profile_name for row in rows}
