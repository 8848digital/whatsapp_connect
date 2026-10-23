# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""The key pair of the Flow data endpoint, one per WhatsApp Account (phone number)."""

import frappe
from frappe.utils.password import set_encrypted_password

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI
from whatsapp_connect.whatsapp_connect_flow import flow_api
from whatsapp_connect.whatsapp_connect_flow.crypto import generate_key_pair


def generate_flow_keys(account: str) -> str:
	"""
	Create a new key pair, store it on the account and register the public key in Meta.

	Parameters:
	        account (str, required): The WhatsApp Account name.

	Returns:
	        str: The public key (PEM).
	"""
	frappe.get_doc("WhatsApp Account", account).check_permission("write")
	private_pem, public_pem = generate_key_pair()
	flow_api.upload_public_key(CloudAPI(account), public_pem)
	set_encrypted_password("WhatsApp Account", account, private_pem, "flow_private_key")
	frappe.db.set_value(
		"WhatsApp Account", account, {"flow_public_key": public_pem, "flow_private_key": "*" * 10}
	)
	return public_pem
