# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Coexistence: messages typed in the WhatsApp Business app on the phone.

When a number is used in the WhatsApp Business app and through the Cloud API,
Meta sends each message typed on the phone as an "smb_message_echoes" event.
They are saved as outgoing messages so the conversation is complete.
"""

import frappe

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_account.account_utils import (
	get_account_by_phone_number_id,
)
from whatsapp_connect.whatsapp_connect_core.messaging.contact_link import find_reference
from whatsapp_connect.whatsapp_connect_core.webhook.common import to_datetime

SAVED_TYPES = ("text", "image", "video", "audio", "document", "sticker")


def handle_echoes_change(value: dict) -> None:
	"""
	Save the echoed messages of one change.

	Parameters:
	        value (dict, required): The change value: metadata and message_echoes.

	Returns:
	        None
	"""
	account = get_account_by_phone_number_id((value.get("metadata") or {}).get("phone_number_id"))
	if not account:
		return
	for echo in value.get("message_echoes") or []:
		if not frappe.db.exists("WhatsApp Message", {"wamid": echo.get("id")}):
			__save(echo, account)


def __save(echo: dict, account: str) -> None:
	"""
	Insert one echoed message as an outgoing message that is not sent again.

	Parameters:
	        echo (dict, required): Meta's echo object.
	        account (str, required): The WhatsApp Account.

	Returns:
	        None
	"""
	message_type = echo.get("type") if echo.get("type") in SAVED_TYPES else "unsupported"
	content = echo.get(echo.get("type") or "") or {}
	message = frappe.get_doc(
		{
			"doctype": "WhatsApp Message",
			"direction": "Outgoing",
			"whatsapp_account": account,
			"phone_number": echo.get("to"),
			"wamid": echo.get("id"),
			"message_type": message_type,
			"body": content.get("body") or content.get("caption"),
			"media_id": content.get("id") if message_type != "text" else None,
			"status": "Sent",
			"sent_at": to_datetime(echo.get("timestamp")),
			"source": "WhatsApp Business App",
		}
	)
	doctype, name = find_reference(echo.get("to"))
	if doctype:
		message.reference_doctype, message.reference_name = doctype, name
	message.flags.skip_send = True
	message.insert(ignore_permissions=True)
