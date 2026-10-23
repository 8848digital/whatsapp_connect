# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import json

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_inbox import inbox_send


@frappe.whitelist(methods=["GET"])
def get_quick_replies():
	"""
	        Enabled WhatsApp Quick Replies, for the reply box.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.send.get_quick_replies`
	        **HTTP Method:** GET
	        **Parameters:** none
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "", "data": [{"title": "Opening hours", "shortcut": "hours", "message": "We are open 9 to 6."}], "errors": null}
	```
	"""
	return api_response(
		data=frappe.get_list(
			"WhatsApp Quick Reply",
			filters={"enabled": 1},
			fields=["title", "shortcut", "message"],
			order_by="title asc",
		)
	)


@frappe.whitelist(methods=["POST"])
def send_text(phone_number: str, text: str, reply_to: str | None = None):
	"""
	        Send free text in a conversation. Allowed only within 24 hours of the customer's last message.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.send.send_text`
	        **HTTP Method:** POST
	        **Parameters:**
	                - phone_number (str, required): The customer's number
	                - text (str, required): The message text
	                - reply_to (str, optional): The WhatsApp Message being answered
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Message status: Sent", "data": {"message": "a1b2c3d4e5", "status": "Sent", "error": null}, "errors": null}
	```
	"""
	return __result(inbox_send.send_text(phone_number, text, reply_to))


@frappe.whitelist(methods=["POST"])
def send_file(phone_number: str, file_url: str, caption: str | None = None):
	"""
	        Send an uploaded file as an image, video, audio or document message.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.send.send_file`
	        **HTTP Method:** POST
	        **Parameters:**
	                - phone_number (str, required): The customer's number
	                - file_url (str, required): URL of a file uploaded to this site
	                - caption (str, optional): Text under images, videos and documents
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Message status: Sent", "data": {"message": "a1b2c3d4e5", "status": "Sent", "error": null}, "errors": null}
	```
	"""
	return __result(inbox_send.send_file(phone_number, file_url, caption))


@frappe.whitelist(methods=["POST"])
def send_template(phone_number: str, template: str, body_values: str | list | None = None):
	"""
	        Send an approved template to a number. This also starts a conversation with a new number.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.send.send_template`
	        **HTTP Method:** POST
	        **Parameters:**
	                - phone_number (str, required): The customer's number with the country code
	                - template (str, required): The WhatsApp Template name
	                - body_values (list, optional): Values for {{1}}, {{2}}... (JSON list); empty uses the linked record or the samples
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Message status: Sent", "data": {"message": "a1b2c3d4e5", "status": "Sent", "error": null}, "errors": null}
	```
	"""
	if isinstance(body_values, str):
		body_values = json.loads(body_values or "[]")
	return __result(inbox_send.send_template_message(phone_number, template, body_values))


def __result(message):
	"""
	Build the response for a sent message; a failed send returns status false with Meta's reason.

	Parameters:
	        message (Document, required): The WhatsApp Message.

	Returns:
	        dict: The standard response envelope.
	"""
	data = {
		"message": message.name,
		"status": message.status,
		"error": message.error_message,
		"phone_number": message.phone_number,
	}
	failed = message.status in ("Failed", "Opted Out")
	return api_response(
		status=not failed,
		code=422 if failed else 200,
		message=message.error_message or _("Message status: {0}").format(_(message.status)),
		data=data,
	)
