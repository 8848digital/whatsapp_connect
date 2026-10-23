# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Frappe CRM's WhatsApp endpoints, served by WhatsApp Connect (override_whitelisted_methods).

These keep the names, parameters and plain return values of crm.api.whatsapp,
because the CRM front end calls them.
"""

import frappe

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_account.account_utils import (
	get_default_account,
)
from whatsapp_connect.whatsapp_connect_crm import crm_messages, crm_send
from whatsapp_connect.whatsapp_connect_crm.crm_access import check_access


@frappe.whitelist()
def is_whatsapp_installed():
	"""
	        Tell Frappe CRM that WhatsApp is available.

	        **Endpoint:** `/api/method/crm.api.whatsapp.is_whatsapp_installed`
	        **HTTP Method:** GET
	        **Parameters:** none
	        **Response:**
	```json
	                {"message": true}
	```
	"""
	return True


@frappe.whitelist()
def is_whatsapp_enabled():
	"""
	        Tell Frappe CRM if a WhatsApp Account can send: an enabled default outgoing account.

	        **Endpoint:** `/api/method/crm.api.whatsapp.is_whatsapp_enabled`
	        **HTTP Method:** GET
	        **Parameters:** none
	        **Response:**
	```json
	                {"message": true}
	```
	"""
	return bool(get_default_account("outgoing"))


@frappe.whitelist()
def get_whatsapp_messages(reference_doctype: str, reference_name: str):
	"""
	        The messages of a CRM Lead or CRM Deal, found by its numbers, oldest first.

	        **Endpoint:** `/api/method/crm.api.whatsapp.get_whatsapp_messages`
	        **HTTP Method:** GET
	        **Parameters:**
	                - reference_doctype (str, required): CRM Lead or CRM Deal
	                - reference_name (str, required): The record name
	        **Response:**
	```json
	                {"message": [{"name": "a1b2c3d4e5", "type": "Incoming", "from": "919900000101", "message": "Hi", "content_type": "text", "status": ""}]}
	```
	"""
	doc = check_access(reference_doctype, reference_name)
	return crm_messages.get_messages(doc)


@frappe.whitelist(methods=["POST"])
def create_whatsapp_message(
	reference_doctype: str,
	reference_name: str,
	message: str,
	to: str,
	attach: str | None = None,
	reply_to: str | None = None,
	content_type: str = "text",
):
	"""
	        Send text or a file from a CRM record. Free text needs a customer message in the last 24 hours.

	        **Endpoint:** `/api/method/crm.api.whatsapp.create_whatsapp_message`
	        **HTTP Method:** POST
	        **Parameters:**
	                - reference_doctype (str, required): CRM Lead or CRM Deal
	                - reference_name (str, required): The record name
	                - message (str, required): The text, or the file URL for a file without caption
	                - to (str, required): The customer's number
	                - attach (str, optional): URL of the file to send
	                - reply_to (str, optional): The WhatsApp Message being answered
	                - content_type (str, optional): text, image, video, audio or document
	        **Response:**
	```json
	                {"message": "a1b2c3d4e5"}
	```
	"""
	doc = check_access(reference_doctype, reference_name)
	return crm_send.send_message(doc, to, message, attach, reply_to, content_type).name


@frappe.whitelist(methods=["POST"])
def send_whatsapp_template(reference_doctype: str, reference_name: str, template: str, to: str):
	"""
	        Send an approved template from a CRM record; its fields fill the variables.

	        **Endpoint:** `/api/method/crm.api.whatsapp.send_whatsapp_template`
	        **HTTP Method:** POST
	        **Parameters:**
	                - reference_doctype (str, required): CRM Lead or CRM Deal
	                - reference_name (str, required): The record name
	                - template (str, required): The WhatsApp Template name
	                - to (str, required): The customer's number
	        **Response:**
	```json
	                {"message": "a1b2c3d4e5"}
	```
	"""
	doc = check_access(reference_doctype, reference_name)
	return crm_send.send_crm_template(doc, template, to).name


@frappe.whitelist(methods=["POST"])
def react_on_whatsapp_message(emoji: str, reply_to_name: str):
	"""
	        React with an emoji to a message the user can see.

	        **Endpoint:** `/api/method/crm.api.whatsapp.react_on_whatsapp_message`
	        **HTTP Method:** POST
	        **Parameters:**
	                - emoji (str, required): The emoji
	                - reply_to_name (str, required): The WhatsApp Message to react to
	        **Response:**
	```json
	                {"message": "a1b2c3d4e5"}
	```
	"""
	target = frappe.db.get_value(
		"WhatsApp Message", reply_to_name, ["reference_doctype", "reference_name"], as_dict=True
	)
	if not target:
		frappe.throw(frappe._("Message {0} not found").format(reply_to_name), frappe.DoesNotExistError)
	check_access(target.reference_doctype, target.reference_name)
	return crm_send.send_reaction(emoji, reply_to_name).name
