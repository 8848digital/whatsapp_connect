# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""The hub's side of Embedded Signup: sessions, code exchange, claim and disconnect.

1. start: a site opens a session and gets a one-time claim secret (server to server).
2. finish: the signup page sends Meta's code; the hub exchanges it for the business
   token, checks the number and subscribes its app to the business account.
3. claim: the site gets the token and its forwarding secret with the claim secret.
   The hub then deletes the token; it keeps only what it needs to forward webhooks.
"""

import hashlib
import hmac
import secrets

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime
from frappe.utils.password import remove_encrypted_password

from whatsapp_connect.whatsapp_connect_setup.graph import TokenGraph
from whatsapp_connect.whatsapp_connect_setup.hub.meta import exchange_code, find_number
from whatsapp_connect.whatsapp_connect_setup.hub.safe_url import check_site_urls
from whatsapp_connect.whatsapp_connect_setup.hub.settings import (
	FLOW_RELAY_PATH,
	SIGNUP_PATH,
	get_hub_settings,
)

DOCTYPE = "WhatsApp Hub Connection"
SESSION_MINUTES = 60
FINISH_EVENTS = {"FINISH", "FINISH_ONLY_WABA", "FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING"}


def start(site_url: str, callback_url: str, flow_url: str, coexistence: int = 0) -> dict:
	"""
	Open a signup session for a site.

	Parameters:
	        site_url (str, required): The site's base URL.
	        callback_url (str, required): The site's webhook URL.
	        flow_url (str, required): The site's Flow endpoint URL.
	        coexistence (int, optional): 1 when the number stays on the WhatsApp Business app.

	Returns:
	        dict: {"session", "claim_secret", "signup_url"}.
	"""
	settings = get_hub_settings()
	check_site_urls(site_url, [callback_url, flow_url], bool(settings.allow_insecure_sites))
	session, claim_secret = secrets.token_hex(16), secrets.token_urlsafe(32)
	frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"name": session,
			"status": "Pending",
			"site_url": site_url.rstrip("/"),
			"callback_url": callback_url,
			"flow_url": flow_url,
			"coexistence": int(bool(int(coexistence or 0))),
			"claim_secret_hash": __hash(claim_secret),
		}
	).insert(ignore_permissions=True)
	return {
		"session": session,
		"claim_secret": claim_secret,
		"signup_url": frappe.utils.get_url(f"{SIGNUP_PATH}?session={session}"),
	}


def finish(session: str, code: str, waba_id: str, phone_number_id: str, event: str) -> dict:
	"""
	Exchange Meta's code for the business token and prepare the connection.

	Parameters:
	        session (str, required): The signup session.
	        code (str, required): The code from Meta's login popup.
	        waba_id (str, required): The business account chosen in the popup.
	        phone_number_id (str, required): The phone number chosen in the popup.
	        event (str, required): The popup's finish event, for example "FINISH".

	Returns:
	        dict: {"site_url", "display_phone_number"} for the signup page.
	"""
	settings = get_hub_settings()
	connection = __open_session(session, "Pending")
	if event not in FINISH_EVENTS or not phone_number_id:
		frappe.throw(_("Choose a phone number in the Meta window to finish the signup"))
	token = exchange_code(settings, code)
	graph = TokenGraph(token, settings.graph_api_url, settings.graph_api_version)
	number = find_number(graph, waba_id, phone_number_id)
	graph.request("POST", f"{waba_id}/subscribed_apps")
	connection.update(
		{
			"status": "Connected",
			"waba_id": waba_id,
			"phone_number_id": phone_number_id,
			"display_phone_number": number.get("display_phone_number"),
			"verified_name": number.get("verified_name"),
			"signup_event": event,
			"access_token": token,
			"forward_secret": secrets.token_urlsafe(32),
		}
	)
	connection.save(ignore_permissions=True)
	return {
		"site_url": connection.site_url,
		"display_phone_number": number.get("display_phone_number"),
	}


def claim(session: str, claim_secret: str) -> dict:
	"""
	Give the site its token and forwarding secret, once, and delete the token on the hub.

	Parameters:
	        session (str, required): The signup session.
	        claim_secret (str, required): The secret that start() gave the site.

	Returns:
	        dict: The values for the site's WhatsApp Account.
	"""
	settings = get_hub_settings()
	connection = __open_session(session, "Connected")
	if not hmac.compare_digest(connection.claim_secret_hash, __hash(claim_secret or "")):
		raise frappe.PermissionError(_("The claim secret does not match"))
	data = {
		"connection": connection.name,
		"access_token": connection.get_password("access_token"),
		"forward_secret": connection.get_password("forward_secret"),
		"app_id": settings.app_id,
		"graph_api_url": settings.graph_api_url,
		"graph_api_version": settings.graph_api_version,
		"waba_id": connection.waba_id,
		"phone_number_id": connection.phone_number_id,
		"display_phone_number": connection.display_phone_number,
		"verified_name": connection.verified_name,
		"signup_event": connection.signup_event,
		"flow_endpoint_url": frappe.utils.get_url(f"{FLOW_RELAY_PATH}?connection={connection.name}"),
	}
	remove_encrypted_password(DOCTYPE, connection.name, "access_token")
	connection.db_set("status", "Claimed")
	__close_older_connections(connection)
	return data


def disconnect(connection: str, signature: str) -> None:
	"""
	Stop forwarding for a connection, when the site proves it holds the forwarding secret.

	Parameters:
	        connection (str, required): The connection name.
	        signature (str, required): HMAC-SHA256 of "disconnect:<connection>" with the secret.

	Returns:
	        None
	"""
	get_hub_settings()
	doc = frappe.get_doc(DOCTYPE, connection)
	secret = doc.get_password("forward_secret", raise_exception=False) or ""
	expected = hmac.new(
		secret.encode(), f"disconnect:{connection}".encode(), hashlib.sha256
	).hexdigest()
	if not secret or not hmac.compare_digest(expected, signature or ""):
		raise frappe.PermissionError(_("The signature does not match"))
	doc.db_set("status", "Disconnected")


def __open_session(session: str, status: str):
	"""
	Load a session that has the expected status and has not expired.

	Parameters:
	        session (str, required): The session name.
	        status (str, required): The status it must have.

	Returns:
	        Document: The WhatsApp Hub Connection.
	"""
	name = frappe.db.get_value(
		DOCTYPE,
		{
			"name": session or "",
			"status": status,
			"creation": [">", add_to_date(now_datetime(), minutes=-SESSION_MINUTES)],
		},
	)
	if not name:
		frappe.throw(_("The signup session is not valid or has expired. Start again from your site."))
	return frappe.get_doc(DOCTYPE, name)


def __close_older_connections(connection) -> None:
	"""
	Disconnect earlier connections of the same site and business account, so webhooks arrive once.

	Parameters:
	        connection (Document, required): The connection that was just claimed.

	Returns:
	        None
	"""
	filters = {
		"name": ["!=", connection.name],
		"site_url": connection.site_url,
		"waba_id": connection.waba_id,
		"status": "Claimed",
	}
	for name in frappe.get_all(DOCTYPE, filters=filters, pluck="name"):
		frappe.db.set_value(DOCTYPE, name, "status", "Disconnected")


def __hash(value: str) -> str:
	"""
	Return the SHA-256 hex digest of a secret.

	Parameters:
	        value (str, required): The secret.

	Returns:
	        str: The hex digest.
	"""
	return hashlib.sha256(value.encode()).hexdigest()
