# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Create the WhatsApp Account from setup values and run the setup steps on it."""

import secrets

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI, CloudAPIError
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_meta import (
	sync_templates,
)
from whatsapp_connect.whatsapp_connect_flow.keys import generate_flow_keys
from whatsapp_connect.whatsapp_connect_setup.discovery import NUMBER_FIELDS
from whatsapp_connect.whatsapp_connect_setup.webhook_setup import subscribe_webhooks

# Meta's error when the number already has another two-step verification PIN.
PIN_MISMATCH_CODES = {133005, 133006}


def save_account(values: dict) -> str:
	"""
	Create the WhatsApp Account of a phone number, or update the one that exists.

	Parameters:
	        values (dict, required): Field values; phone_number_id and business_account_id are required.
	                "verified_name" names a new account.

	Returns:
	        str: The WhatsApp Account name.
	"""
	values = dict(values)
	verified_name = values.pop("verified_name", None)
	name = frappe.db.get_value("WhatsApp Account", {"phone_number_id": values["phone_number_id"]})
	account = frappe.get_doc("WhatsApp Account", name) if name else frappe.new_doc("WhatsApp Account")
	account.update({key: value for key, value in values.items() if value is not None})
	account.enabled = 1
	if not name:
		account.account_name = __unique_name(verified_name or values.get("display_phone_number"))
		account.verify_token = frappe.generate_hash(length=32)
		has_default = frappe.db.exists("WhatsApp Account", {"enabled": 1, "default_outgoing": 1})
		account.default_outgoing = account.default_incoming = int(not has_default)
	account.save(ignore_permissions=True)
	return account.name


def run_setup_steps(account: str, register_number: bool) -> list[dict]:
	"""
	Check the number, register it, subscribe webhooks, sync templates and create Flow keys.

	A failed step does not stop the next ones; each step reports its own result.

	Parameters:
	        account (str, required): The WhatsApp Account name.
	        register_number (bool, required): Register the number for the Cloud API (new numbers).

	Returns:
	        list[dict]: One {"step", "ok", "message"} per step.
	"""
	steps = [
		(_("Check the phone number"), lambda: check_number(account)),
		(_("Register the number"), lambda: register(account) if register_number else _("Not needed")),
		(_("Connect webhooks"), lambda: subscribe_webhooks(account)),
		(_("Sync templates"), lambda: __sync_templates(account)),
		(_("Create Flow keys"), lambda: __flow_keys(account)),
	]
	return [__run(label, step) for label, step in steps]


def check_number(account: str) -> str:
	"""
	Read the number from Meta with the account's token and save its display number.

	Parameters:
	        account (str, required): The WhatsApp Account name.

	Returns:
	        str: For example "+91 98765 43210 (Asha Traders), quality GREEN".
	"""
	doc = frappe.get_doc("WhatsApp Account", account)
	number = CloudAPI(doc).request("GET", doc.phone_number_id, params={"fields": NUMBER_FIELDS})
	doc.db_set("display_phone_number", number.get("display_phone_number"))
	return _("{0} ({1}), quality {2}").format(
		number.get("display_phone_number"),
		number.get("verified_name"),
		number.get("quality_rating") or _("not rated yet"),
	)


def register(account: str) -> str:
	"""
	Register the number for the Cloud API with its two-step verification PIN.

	A new 6-digit PIN is created and saved when the account has none.

	Parameters:
	        account (str, required): The WhatsApp Account name.

	Returns:
	        str: A confirmation.
	"""
	doc = frappe.get_doc("WhatsApp Account", account)
	pin = doc.get_password("registration_pin", raise_exception=False)
	if not pin:
		pin = "".join(secrets.choice("0123456789") for _ in range(6))
		doc.registration_pin = pin
		doc.save(ignore_permissions=True)
	body = {"messaging_product": "whatsapp", "pin": pin}
	try:
		CloudAPI(doc).request("POST", f"{doc.phone_number_id}/register", json_body=body, log_body=False)
	except CloudAPIError as exc:
		if exc.code in PIN_MISMATCH_CODES:
			frappe.throw(
				_(
					"The number already has a two-step verification PIN. Enter it in WhatsApp Account > Two-Step Verification PIN and run the setup again."
				)
			)
		raise
	return _("Registered; the PIN is saved on the WhatsApp Account")


def __run(label: str, step) -> dict:
	"""
	Run one step and turn its result or error into a step result.

	Parameters:
	        label (str, required): The step name shown to the user.
	        step (callable, required): Returns a message, or raises.

	Returns:
	        dict: {"step", "ok", "message"}.
	"""
	try:
		return {"step": label, "ok": True, "message": step()}
	except CloudAPIError as exc:
		return {"step": label, "ok": False, "message": exc.describe()}
	except frappe.ValidationError as exc:
		return {"step": label, "ok": False, "message": str(exc)}


def __sync_templates(account: str) -> str:
	"""
	Sync the account's templates from Meta.

	Parameters:
	        account (str, required): The WhatsApp Account name.

	Returns:
	        str: How many templates were synced.
	"""
	return _("{0} templates synced").format(sync_templates(account))


def __flow_keys(account: str) -> str:
	"""
	Create the Flow endpoint key pair when the account has none.

	Parameters:
	        account (str, required): The WhatsApp Account name.

	Returns:
	        str: What was done.
	"""
	if frappe.db.get_value("WhatsApp Account", account, "flow_public_key"):
		return _("The account already has Flow keys")
	generate_flow_keys(account)
	return _("Created and registered in Meta")


def __unique_name(base: str | None) -> str:
	"""
	Return an account name that is not used yet.

	Parameters:
	        base (str, optional): The preferred name, for example the verified business name.

	Returns:
	        str: The base name, or the base name with a number.
	"""
	base = (base or _("WhatsApp")).strip()
	name, number = base, 2
	while frappe.db.exists("WhatsApp Account", name):
		name, number = f"{base} {number}", number + 1
	return name
