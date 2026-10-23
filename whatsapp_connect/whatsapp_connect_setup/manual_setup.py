# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Connect a number with the customer's own Meta app (guided manual setup)."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_setup.account_setup import run_setup_steps, save_account
from whatsapp_connect.whatsapp_connect_setup.discovery import discover


def connect_own_app(
	app_id: str,
	app_secret: str,
	access_token: str,
	phone_number_id: str,
	register_number: bool = False,
) -> dict:
	"""
	Check the credentials, save the WhatsApp Account and run the setup steps.

	Parameters:
	        app_id (str, required): The Meta App ID.
	        app_secret (str, required): The Meta App Secret.
	        access_token (str, required): A system user token of the app.
	        phone_number_id (str, required): The number to connect, from discover().
	        register_number (bool, optional): Register the number for the Cloud API.

	Returns:
	        dict: {"account", "steps", "expires_at"}.
	"""
	found = discover(app_id, app_secret, access_token)
	waba, number = __find_number(found["accounts"], phone_number_id)
	account = save_account(
		{
			"setup_method": "Manual",
			"hub_connection": "",
			"flow_endpoint_url": "",
			"app_id": app_id,
			"app_secret": app_secret,
			"access_token": access_token,
			"business_account_id": waba["id"],
			"phone_number_id": number["id"],
			"display_phone_number": number.get("display_phone_number"),
			"verified_name": number.get("verified_name"),
		}
	)
	# Meta calls the webhook with the verify token while the webhook is set,
	# from another request, so the account must be in the database first.
	frappe.db.commit()  # nosemgrep
	steps = run_setup_steps(account, bool(int(register_number or 0)))
	return {"account": account, "steps": steps, "expires_at": found["expires_at"]}


def __find_number(accounts: list[dict], phone_number_id: str) -> tuple[dict, dict]:
	"""
	Find a phone number and its business account in the discovered accounts.

	Parameters:
	        accounts (list[dict], required): The "accounts" of discover().
	        phone_number_id (str, required): The phone number ID.

	Returns:
	        tuple[dict, dict]: The business account and the phone number.
	"""
	for waba in accounts:
		for number in waba["phone_numbers"]:
			if number["id"] == phone_number_id:
				return waba, number
	frappe.throw(_("The token cannot use the phone number {0}").format(phone_number_id))
