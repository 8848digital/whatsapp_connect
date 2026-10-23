# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Business logic for WhatsApp Account."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI

DEFAULT_FIELDS = {"outgoing": "default_outgoing", "incoming": "default_incoming"}


def validate_account(account) -> None:
	"""
	Clean the Graph API URL and check the API version format.

	Parameters:
	        account (Document, required): The WhatsApp Account being saved.

	Returns:
	        None
	"""
	account.graph_api_url = (account.graph_api_url or "").strip().rstrip("/")
	version = (account.graph_api_version or "").strip()
	if not version.startswith("v"):
		version = f"v{version}"
	account.graph_api_version = version


def clear_other_defaults(account) -> None:
	"""
	Unset the default flags on other accounts when this account is a default.

	Parameters:
	        account (Document, required): The saved WhatsApp Account.

	Returns:
	        None
	"""
	for fieldname in DEFAULT_FIELDS.values():
		if account.get(fieldname):
			frappe.db.set_value(
				"WhatsApp Account",
				{"name": ["!=", account.name], fieldname: 1},
				fieldname,
				0,
			)


def get_default_account(direction: str = "outgoing") -> str | None:
	"""
	Return the enabled default account for a direction, or the only enabled account.

	Parameters:
	        direction (str, optional): "outgoing" or "incoming". Default "outgoing".

	Returns:
	        str | None: The WhatsApp Account name, or None when there is no usable account.
	"""
	fieldname = DEFAULT_FIELDS[direction]
	account = frappe.db.get_value("WhatsApp Account", {"enabled": 1, fieldname: 1})
	if account:
		return account
	enabled = frappe.get_all("WhatsApp Account", filters={"enabled": 1}, pluck="name", limit=2)
	return enabled[0] if len(enabled) == 1 else None


def get_account_by_phone_number_id(phone_number_id: str | None) -> str | None:
	"""
	Find the enabled account that owns a Meta phone number ID (from webhook metadata).

	Parameters:
	        phone_number_id (str, optional): The phone_number_id sent by Meta.

	Returns:
	        str | None: The WhatsApp Account name, or None when it is unknown or disabled.
	"""
	if not phone_number_id:
		return None
	return frappe.db.get_value("WhatsApp Account", {"phone_number_id": phone_number_id, "enabled": 1})


def subscribe_app(account_name: str) -> dict:
	"""
	Subscribe the Meta app to the account's WhatsApp Business Account.

	Parameters:
	        account_name (str, required): The WhatsApp Account name.

	Returns:
	        dict: Meta's answer.
	"""
	frappe.get_doc("WhatsApp Account", account_name).check_permission("write")
	answer = CloudAPI(account_name).subscribe_app()
	if not answer.get("success"):
		frappe.throw(_("Meta did not confirm the subscription: {0}").format(frappe.as_json(answer)))
	return answer
