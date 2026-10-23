# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_account import account_utils


@frappe.whitelist(methods=["POST"])
def subscribe_app(account: str):
	"""
	        Subscribe the Meta app to the account's WhatsApp Business Account, so that
	        Meta sends webhooks for it. Needed once after connecting a number.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.account.subscribe_app`
	        **HTTP Method:** POST
	        **Parameters:**
	                - account (str, required): The WhatsApp Account name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "The app is subscribed to webhooks",
	                        "data": {"success": true},
	                        "errors": null
	                }
	```
	"""
	answer = account_utils.subscribe_app(account)
	return api_response(message=_("The app is subscribed to webhooks"), data=answer)
