# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Tests that the WhatsApp Setup page runs on a connected account."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.messaging.template_send import send_template

TEST_TEMPLATE = "hello_world"
ACCOUNT_FIELDS = [
	"name",
	"display_phone_number",
	"setup_method",
	"enabled",
	"default_outgoing",
	"default_incoming",
]


def list_accounts() -> dict:
	"""
	Return the WhatsApp Accounts and whether Connect with Facebook is available.

	Returns:
	        dict: {"accounts": [...], "hub_url": str | None, "site_url": str}.
	"""
	return {
		"accounts": frappe.get_all("WhatsApp Account", fields=ACCOUNT_FIELDS, order_by="creation"),
		"hub_url": frappe.db.get_single_value("WhatsApp Settings", "hub_url"),
		"site_url": frappe.utils.get_url(),
	}


def send_test(account: str, to: str) -> dict:
	"""
	Send the hello_world template of the account to a number.

	Parameters:
	        account (str, required): The WhatsApp Account name.
	        to (str, required): The phone number, with the country code.

	Returns:
	        dict: {"message": WhatsApp Message name, "status": its status}.
	"""
	template = frappe.db.get_value(
		"WhatsApp Template",
		{"whatsapp_account": account, "template_name": TEST_TEMPLATE, "status": "Approved"},
	)
	if not template:
		frappe.throw(
			_(
				"The account has no approved {0} template. Click Sync Templates, or send a message from your phone and use Check Incoming instead."
			).format(TEST_TEMPLATE)
		)
	message = send_template(template, to, account=account, source=_("WhatsApp Setup test"))
	if message.status == "Failed":
		frappe.throw(_("Meta refused the message: {0}").format(message.error_message))
	return {"message": message.name, "status": message.status}


def incoming_since(account: str, since: str) -> dict:
	"""
	Look for a message that the account received after a time.

	Parameters:
	        account (str, required): The WhatsApp Account name.
	        since (str, required): Datetime in the site's time zone.

	Returns:
	        dict: {"found": bool, "phone_number", "body"} of the first message after the time.
	"""
	messages = frappe.get_all(
		"WhatsApp Message",
		filters={"whatsapp_account": account, "direction": "Incoming", "creation": [">=", since]},
		fields=["phone_number", "body"],
		order_by="creation asc",
		limit=1,
	)
	return {"found": bool(messages), **(messages[0] if messages else {})}
