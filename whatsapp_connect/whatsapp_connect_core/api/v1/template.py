# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template import template_meta
from whatsapp_connect.whatsapp_connect_core.messaging.template_preview import render_preview


@frappe.whitelist(methods=["POST"])
def submit(template: str):
	"""
	        Send a WhatsApp Template to Meta for approval: create it, or update it when
	        Meta already has it. Media headers upload the sample file first.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.template.submit`
	        **HTTP Method:** POST
	        **Parameters:**
	                - template (str, required): The WhatsApp Template name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Sent to Meta. Status: Pending",
	                        "data": {"status": "Pending"},
	                        "errors": null
	                }
	```
	"""
	status = template_meta.submit_template(template)
	return api_response(
		message=_("Sent to Meta. Status: {0}").format(_(status)), data={"status": status}
	)


@frappe.whitelist(methods=["POST"])
def sync(account: str):
	"""
	        Create or update local WhatsApp Templates from all templates of an account in Meta.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.template.sync`
	        **HTTP Method:** POST
	        **Parameters:**
	                - account (str, required): The WhatsApp Account name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "12 templates synced from Meta",
	                        "data": {"count": 12},
	                        "errors": null
	                }
	```
	"""
	count = template_meta.sync_templates(account)
	return api_response(
		message=_("{0} templates synced from Meta").format(count), data={"count": count}
	)


@frappe.whitelist()
def preview(template: str, doctype: str | None = None, name: str | None = None):
	"""
	        Return the template as the customer will see it, with the variables filled
	        from a document (or the samples when no document is given).

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.template.preview`
	        **HTTP Method:** GET
	        **Parameters:**
	                - template (str, required): The WhatsApp Template name
	                - doctype (str, optional): Doctype of the document that fills the variables
	                - name (str, optional): Name of that document
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "",
	                        "data": {"header": "Order SO-0001", "header_type": "Text", "body": "Hello Asha...", "footer": "...", "buttons": ["Track order"]},
	                        "errors": null
	                }
	```
	"""
	return api_response(data=render_preview(template, doctype, name))
