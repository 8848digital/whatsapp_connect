# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Find the WhatsApp Business Accounts and phone numbers that a token can use."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_setup.graph import TokenGraph, app_graph

WABA_SCOPES = ("whatsapp_business_management", "whatsapp_business_messaging")
NUMBER_FIELDS = "id,display_phone_number,verified_name,quality_rating,code_verification_status"


def discover(app_id: str, app_secret: str, access_token: str) -> dict:
	"""
	Check a token and list the business accounts and numbers it gives access to.

	Parameters:
	        app_id (str, required): The Meta App ID.
	        app_secret (str, required): The Meta App Secret.
	        access_token (str, required): A system user token of the app.

	Returns:
	        dict: {"expires_at": 0 for never, "accounts": [{"id", "name", "phone_numbers": [...]}]}.
	"""
	info = inspect_token(app_id, app_secret, access_token)
	graph = TokenGraph(access_token)
	accounts = []
	for waba_id in __waba_ids(info):
		waba = graph.request("GET", waba_id, params={"fields": "id,name"})
		numbers = graph.request("GET", f"{waba_id}/phone_numbers", params={"fields": NUMBER_FIELDS})
		accounts.append({**waba, "phone_numbers": numbers.get("data") or []})
	return {"expires_at": info.get("expires_at") or 0, "accounts": accounts}


def inspect_token(app_id: str, app_secret: str, access_token: str) -> dict:
	"""
	Ask Meta about a token (debug_token) and check that it is valid and belongs to the app.

	Parameters:
	        app_id (str, required): The Meta App ID.
	        app_secret (str, required): The Meta App Secret.
	        access_token (str, required): The token to check.

	Returns:
	        dict: Meta's token data: is_valid, app_id, expires_at, scopes, granular_scopes.
	"""
	answer = app_graph(app_id, app_secret).request(
		"GET", "debug_token", params={"input_token": access_token}
	)
	info = answer.get("data") or {}
	if not info.get("is_valid"):
		message = (info.get("error") or {}).get("message") or ""
		frappe.throw(_("The access token is not valid. {0}").format(message))
	if str(info.get("app_id")) != str(app_id):
		frappe.throw(_("The access token belongs to another Meta app ({0}).").format(info.get("app_id")))
	missing = [scope for scope in WABA_SCOPES if scope not in (info.get("scopes") or [])]
	if missing:
		frappe.throw(_("Give the token these permissions: {0}").format(", ".join(missing)))
	return info


def __waba_ids(info: dict) -> list[str]:
	"""
	Return the business account IDs that the token's WhatsApp permissions cover.

	Parameters:
	        info (dict, required): Meta's debug_token data.

	Returns:
	        list[str]: WhatsApp Business Account IDs, without duplicates.
	"""
	ids = []
	for scope in info.get("granular_scopes") or []:
		if scope.get("scope") in WABA_SCOPES:
			ids.extend(i for i in scope.get("target_ids") or [] if i not in ids)
	if not ids:
		frappe.throw(
			_(
				"The token has no WhatsApp Business Account. In Meta Business Settings, assign the account to the system user, then generate the token again."
			)
		)
	return ids
