# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Send an outgoing WhatsApp Message and record Meta's answer on it."""

import frappe
from frappe.utils import now_datetime

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI, CloudAPIError
from whatsapp_connect.whatsapp_connect_core.messaging.opt_out import is_opted_out
from whatsapp_connect.whatsapp_connect_core.messaging.payload import build_payload

# Business-initiated messages that must not go to opted-out numbers.
BLOCKED_WHEN_OPTED_OUT = ("template",)


def send(message) -> bool:
	"""
	Send the message now. On an error, the message is kept with the status Failed.

	Parameters:
	        message (Document, required): An inserted outgoing WhatsApp Message.

	Returns:
	        bool: True when Meta accepted the message.
	"""
	if message.message_type in BLOCKED_WHEN_OPTED_OUT and is_opted_out(message.phone_number):
		message.db_set("status", "Opted Out")
		return False

	try:
		api = CloudAPI(message.whatsapp_account)
		payload = build_payload(message, api)
		wamid = api.send_message(payload)
	except CloudAPIError as error:
		message.flags.cloud_api_error = error
		message.db_set(
			{
				"status": "Failed",
				"error_code": str(error.code or ""),
				"error_message": error.describe(),
				"media_id": message.media_id,
			}
		)
		return False

	message.db_set(
		{
			"status": "Sent",
			"wamid": wamid,
			"sent_at": now_datetime(),
			"media_id": message.media_id,
			"error_code": None,
			"error_message": None,
		}
	)
	return True
