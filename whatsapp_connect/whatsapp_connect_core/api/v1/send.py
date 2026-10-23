# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_core.messaging import send_dialog


@frappe.whitelist()
def options(doctype: str, name: str):
	"""
	        Numbers offered in the Send WhatsApp dialog: the document's phone fields and its
	        contacts' numbers, each with the state of the 24-hour reply window.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.send.options`
	        **HTTP Method:** GET
	        **Parameters:**
	                - doctype (str, required): Doctype of the open form
	                - name (str, required): Name of the document
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "",
	                        "data": [{"number": "919900000101", "label": "919900000101 · Mobile No", "window_open": true}],
	                        "errors": null
	                }
	```
	"""
	return api_response(data=send_dialog.get_send_options(doctype, name))


@frappe.whitelist(methods=["POST"])
def send_template_message(template: str, to: str, doctype: str, name: str):
	"""
	        Send an approved template from a document; its fields fill the variables and the
	        message is linked to the document.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.send.send_template_message`
	        **HTTP Method:** POST
	        **Parameters:**
	                - template (str, required): The WhatsApp Template name
	                - to (str, required): The recipient's number
	                - doctype (str, required): Doctype of the document
	                - name (str, required): Name of the document
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Message status: Sent",
	                        "data": {"message": "a1b2c3d4e5", "status": "Sent", "error": null},
	                        "errors": null
	                }
	```
	"""
	message = send_dialog.send_template_to(template, to, doctype, name)
	return __result(message)


@frappe.whitelist(methods=["POST"])
def send_reply_message(to: str, text: str, doctype: str | None = None, name: str | None = None):
	"""
	        Send a free-text reply. Allowed only within 24 hours of the customer's last message.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.send.send_reply_message`
	        **HTTP Method:** POST
	        **Parameters:**
	                - to (str, required): The customer's number
	                - text (str, required): The reply text
	                - doctype (str, optional): Doctype of the document the reply belongs to
	                - name (str, optional): Name of that document
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Message status: Sent",
	                        "data": {"message": "a1b2c3d4e5", "status": "Sent", "error": null},
	                        "errors": null
	                }
	```
	"""
	message = send_dialog.send_reply(to, text, doctype, name)
	return __result(message)


def __result(message):
	"""
	Build the response for a sent message; a failed send returns status false with Meta's reason.

	Parameters:
	        message (Document, required): The WhatsApp Message.

	Returns:
	        dict: The standard response envelope.
	"""
	data = {"message": message.name, "status": message.status, "error": message.error_message}
	failed = message.status in ("Failed", "Opted Out")
	return api_response(
		status=not failed,
		code=422 if failed else 200,
		message=message.error_message or _("Message status: {0}").format(_(message.status)),
		data=data,
	)
