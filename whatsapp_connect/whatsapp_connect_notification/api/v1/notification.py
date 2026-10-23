# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_notification.sending import send_notification


@frappe.whitelist(methods=["POST"])
def send_now(notification: str, docname: str | None = None):
	"""
	        Send a WhatsApp Notification now, for one document (or without one for a
	        scheduled notification), to test it. The condition still applies.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_notification.api.v1.notification.send_now`
	        **HTTP Method:** POST
	        **Parameters:**
	                - notification (str, required): The WhatsApp Notification name
	                - docname (str, optional): Name of a document of the notification's document type
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "2 messages sent",
	                        "data": {"sent": 2},
	                        "errors": null
	                }
	```
	"""
	settings = frappe.get_doc("WhatsApp Notification", notification)
	settings.check_permission("write")
	if docname:
		frappe.get_doc(settings.reference_doctype, docname).check_permission("read")
	sent = send_notification(notification, settings.reference_doctype if docname else None, docname)
	return api_response(message=_("{0} messages sent").format(sent), data={"sent": sent})
