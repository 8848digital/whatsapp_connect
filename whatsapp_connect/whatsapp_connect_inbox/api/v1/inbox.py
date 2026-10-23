# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_inbox import assignment, conversations


@frappe.whitelist(methods=["GET"])
def get_conversations(
	status: str | None = None,
	assigned_to: str | None = None,
	account: str | None = None,
	search: str | None = None,
	start: int = 0,
	page_length: int = 50,
):
	"""
	        Conversations of the WhatsApp Inbox, newest first, and the count of each status.
	        A conversation starts when the customer writes or an agent sends a template from the inbox.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.inbox.get_conversations`
	        **HTTP Method:** GET
	        **Parameters:**
	                - status (str, optional): Open, Pending or Closed; all when empty
	                - assigned_to (str, optional): A user, "me" or "unassigned"
	                - account (str, optional): A WhatsApp Account
	                - search (str, optional): Part of the number or the WhatsApp name
	                - start (int, optional): Rows to skip
	                - page_length (int, optional): Rows to return, at most 100
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "",
	                        "data": {
	                                "conversations": [{"phone_number": "919900000101", "display_name": "Asha", "unread_count": 2, "conversation_status": "Open", "window_open": true}],
	                                "counts": {"Open": 1, "Pending": 0, "Closed": 4}
	                        },
	                        "errors": null
	                }
	```
	"""
	return api_response(
		data=conversations.list_conversations(status, assigned_to, account, search, start, page_length)
	)


@frappe.whitelist(methods=["GET"])
def get_conversation(phone_number: str, before: str | None = None, limit: int = 50):
	"""
	        One conversation with its latest messages (oldest first) and the record it belongs to.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.inbox.get_conversation`
	        **HTTP Method:** GET
	        **Parameters:**
	                - phone_number (str, required): The customer's number
	                - before (str, optional): Only messages created before this time, for older pages
	                - limit (int, optional): Messages to return, at most 100
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "",
	                        "data": {
	                                "conversation": {"phone_number": "919900000101", "window_expires_at": "2026-10-25 09:30:00"},
	                                "messages": [{"name": "a1b2c3d4e5", "direction": "Incoming", "message_type": "text", "body": "Hi"}],
	                                "reference": {"doctype": "Lead", "name": "CRM-LEAD-2026-00001"}
	                        },
	                        "errors": null
	                }
	```
	"""
	return api_response(data=conversations.get_conversation(phone_number, before, limit))


@frappe.whitelist(methods=["POST"])
def mark_read(phone_number: str):
	"""
	        Set the unread count of a conversation to zero.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.inbox.mark_read`
	        **HTTP Method:** POST
	        **Parameters:**
	                - phone_number (str, required): The customer's number
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "", "data": null, "errors": null}
	```
	"""
	conversations.mark_read(phone_number)
	return api_response()


@frappe.whitelist(methods=["POST"])
def set_status(phone_number: str, status: str):
	"""
	        Set a conversation to Open, Pending or Closed.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.inbox.set_status`
	        **HTTP Method:** POST
	        **Parameters:**
	                - phone_number (str, required): The customer's number
	                - status (str, required): Open, Pending or Closed
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Conversation is Closed", "data": null, "errors": null}
	```
	"""
	conversations.set_status(phone_number, status)
	return api_response(message=_("Conversation is {0}").format(_(status)))


@frappe.whitelist(methods=["POST"])
def assign(phone_number: str, user: str | None = None):
	"""
	        Assign a conversation to a user with a WhatsApp role, or remove the assignment.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.inbox.assign`
	        **HTTP Method:** POST
	        **Parameters:**
	                - phone_number (str, required): The customer's number
	                - user (str, optional): The user; empty removes the assignment
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Assigned", "data": null, "errors": null}
	```
	"""
	assignment.assign(phone_number, user)
	return api_response(message=_("Assigned") if user else _("Assignment removed"))


@frappe.whitelist(methods=["GET"])
def get_agents():
	"""
	        Enabled users who can use the WhatsApp Inbox, for the assign menu.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_inbox.api.v1.inbox.get_agents`
	        **HTTP Method:** GET
	        **Parameters:** none
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "", "data": [{"name": "asha@example.com", "full_name": "Asha Rao"}], "errors": null}
	```
	"""
	return api_response(data=assignment.get_agents())
