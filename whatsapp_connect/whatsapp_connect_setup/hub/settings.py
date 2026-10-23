# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Access to WhatsApp Hub Settings for the hub endpoints."""

import frappe
from frappe import _

FLOW_RELAY_PATH = "/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub.flow_endpoint"
SIGNUP_PATH = "/whatsapp_signup"


def get_hub_settings():
	"""
	Return WhatsApp Hub Settings, or stop when this site is not a hub.

	Returns:
	        Document: The enabled WhatsApp Hub Settings.
	"""
	settings = frappe.get_cached_doc("WhatsApp Hub Settings")
	if not settings.enabled:
		raise frappe.PermissionError(_("This site is not a WhatsApp hub"))
	return settings


def get_app_secret() -> str:
	"""
	Return the App Secret of the hub's Meta app.

	Returns:
	        str: The App Secret.
	"""
	return get_hub_settings().get_password("app_secret")
