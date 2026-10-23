# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_automation.actions import get_actions as registered_actions


@frappe.whitelist(methods=["GET"])
def get_actions():
	"""
	        Names of the auto-reply actions, for the Action field of WhatsApp Auto Reply.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_automation.api.v1.auto_reply.get_actions`
	        **HTTP Method:** GET
	        **Parameters:** none
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "", "data": ["Order Status", "Outstanding Balance"], "errors": null}
	```
	"""
	frappe.has_permission("WhatsApp Auto Reply", "read", throw=True)
	return api_response(data=sorted(registered_actions()))
