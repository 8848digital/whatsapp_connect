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

	Errors are Meta's answers (CloudAPIError) or problems found while building the
	message, for example a template that is not approved.

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
	except frappe.ValidationError as error:
		# Keep the reason on the message instead of showing it as a popup.
		frappe.clear_last_message()
		message.flags.send_error = error
		message.db_set(
			{
				"status": "Failed",
				"error_code": str(getattr(error, "code", None) or ""),
				"error_message": error.describe() if isinstance(error, CloudAPIError) else str(error),
				**__built_values(message),
			}
		)
		return False

	message.db_set(
		{
			"status": "Sent",
			"wamid": wamid,
			"sent_at": now_datetime(),
			"error_code": None,
			"error_message": None,
			**__built_values(message),
		}
	)
	return True


def __built_values(message) -> dict:
	"""
	Values filled while the payload was built, saved for reference.

	Parameters:
	        message (Document, required): The WhatsApp Message.

	Returns:
	        dict: media_id and template_params.
	"""
	return {"media_id": message.media_id, "template_params": message.template_params}
