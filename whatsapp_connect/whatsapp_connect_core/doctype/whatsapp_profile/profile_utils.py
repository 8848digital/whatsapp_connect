# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Business logic for WhatsApp Profile."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.phone import normalize_number


def validate_profile(profile) -> None:
	"""
	Normalize the phone number and refuse numbers that cannot be used.

	Parameters:
	        profile (Document, required): The WhatsApp Profile being saved.

	Returns:
	        None
	"""
	number = normalize_number(profile.phone_number)
	if not number:
		frappe.throw(_("{0} is not a valid phone number").format(profile.phone_number))
	profile.phone_number = number


def get_or_create_profile(
	number: str, profile_name: str | None = None, account: str | None = None
) -> str:
	"""
	Return the profile for a number, creating it when it does not exist.

	Parameters:
	        number (str, required): Digits-only phone number.
	        profile_name (str, optional): The customer's WhatsApp name.
	        account (str, optional): The WhatsApp Account that talks to this number.

	Returns:
	        str: The WhatsApp Profile name (its phone number).
	"""
	if frappe.db.exists("WhatsApp Profile", number):
		if profile_name:
			frappe.db.set_value(
				"WhatsApp Profile", number, "profile_name", profile_name, update_modified=False
			)
		return number

	profile = frappe.get_doc(
		{
			"doctype": "WhatsApp Profile",
			"phone_number": number,
			"profile_name": profile_name,
			"whatsapp_account": account,
		}
	)
	profile.insert(ignore_permissions=True)
	return profile.name


def record_incoming(
	number: str, profile_name: str | None, account: str | None, received_at
) -> str:
	"""
	Note that the customer wrote, which opens the 24-hour free-text window.

	Parameters:
	        number (str, required): Digits-only phone number.
	        profile_name (str, optional): The customer's WhatsApp name.
	        account (str, optional): The receiving WhatsApp Account.
	        received_at (datetime, required): When the message was sent by the customer.

	Returns:
	        str: The WhatsApp Profile name.
	"""
	name = get_or_create_profile(number, profile_name, account)
	frappe.db.set_value(
		"WhatsApp Profile", name, "last_incoming_at", received_at, update_modified=False
	)
	return name
