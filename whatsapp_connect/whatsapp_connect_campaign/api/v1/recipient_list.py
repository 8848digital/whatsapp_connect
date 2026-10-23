# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_campaign.doctype.whatsapp_recipient_list import (
	recipient_list_utils,
)


@frappe.whitelist(methods=["POST"])
def import_recipients(recipient_list: str):
	"""
	        Add the records of the list's Document Type (with its filters) as recipients,
	        with their phone, name and variable fields.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_campaign.api.v1.recipient_list.import_recipients`
	        **HTTP Method:** POST
	        **Parameters:**
	                - recipient_list (str, required): The WhatsApp Recipient List name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "The list has 120 recipients",
	                        "data": {"count": 120},
	                        "errors": null
	                }
	```
	"""
	count = recipient_list_utils.import_recipients(recipient_list)
	return api_response(message=_("The list has {0} recipients").format(count), data={"count": count})
