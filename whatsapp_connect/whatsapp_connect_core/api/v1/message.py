# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_message import message_utils


@frappe.whitelist(methods=["POST"])
def retry(message: str):
	"""
	        Send a failed outgoing WhatsApp Message again.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.message.retry`
	        **HTTP Method:** POST
	        **Parameters:**
	                - message (str, required): The WhatsApp Message name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Message status: Sent",
	                        "data": {"status": "Sent"},
	                        "errors": null
	                }
	```
	"""
	status = message_utils.retry_message(message)
	return api_response(message=_("Message status: {0}").format(_(status)), data={"status": status})


@frappe.whitelist(methods=["POST"])
def mark_as_read(message: str):
	"""
	        Mark a received WhatsApp Message as read in the customer's WhatsApp.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.message.mark_as_read`
	        **HTTP Method:** POST
	        **Parameters:**
	                - message (str, required): The WhatsApp Message name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Marked as read",
	                        "data": null,
	                        "errors": null
	                }
	```
	"""
	message_utils.mark_as_read(message)
	return api_response(message=_("Marked as read"))
