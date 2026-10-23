# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Connect with Facebook: this site's side of the Embedded Signup through the 8848 hub."""

import hashlib
import hmac
import json

import requests

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_setup.account_setup import run_setup_steps, save_account
from whatsapp_connect.whatsapp_connect_setup.graph import FLOW_ENDPOINT_PATH, WEBHOOK_PATH

HUB_API = "/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub."
CACHE_KEY = "whatsapp_connect:hub_claim:"
SESSION_SECONDS = 60 * 60
TIMEOUT_SECONDS = 30
# Numbers that stay on the WhatsApp Business app must not be registered again.
COEXISTENCE_EVENT = "FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING"


def start_signup(coexistence: bool = False) -> dict:
	"""
	Open a signup session on the hub and keep its claim secret on the server.

	Parameters:
	        coexistence (bool, optional): The number stays on the WhatsApp Business app.

	Returns:
	        dict: {"session", "signup_url"}: the browser opens signup_url in a popup.
	"""
	data = call_hub(
		"start",
		{
			"site_url": frappe.utils.get_url(),
			"callback_url": frappe.utils.get_url(WEBHOOK_PATH),
			"flow_url": frappe.utils.get_url(FLOW_ENDPOINT_PATH),
			"coexistence": int(bool(int(coexistence or 0))),
		},
	)
	frappe.cache().set_value(
		CACHE_KEY + data["session"], data["claim_secret"], expires_in_sec=SESSION_SECONDS
	)
	return {"session": data["session"], "signup_url": data["signup_url"]}


def complete_signup(session: str) -> dict:
	"""
	Claim the finished signup from the hub, save the account and run the setup steps.

	Parameters:
	        session (str, required): The session from start_signup().

	Returns:
	        dict: {"account", "steps"}.
	"""
	claim_secret = frappe.cache().get_value(CACHE_KEY + session)
	if not claim_secret:
		frappe.throw(_("The signup session has expired. Click Connect with Facebook again."))
	data = call_hub("claim", {"session": session, "claim_secret": claim_secret})
	account = save_account(
		{
			"setup_method": "Embedded Signup",
			"hub_connection": data["connection"],
			"app_id": data["app_id"],
			"app_secret": data["forward_secret"],
			"access_token": data["access_token"],
			"business_account_id": data["waba_id"],
			"phone_number_id": data["phone_number_id"],
			"display_phone_number": data.get("display_phone_number"),
			"verified_name": data.get("verified_name"),
			"graph_api_url": data.get("graph_api_url"),
			"graph_api_version": data.get("graph_api_version"),
			"flow_endpoint_url": data.get("flow_endpoint_url"),
		}
	)
	frappe.cache().delete_value(CACHE_KEY + session)
	steps = run_setup_steps(account, data.get("signup_event") != COEXISTENCE_EVENT)
	return {"account": account, "steps": steps}


def disconnect(account: str) -> None:
	"""
	Ask the hub to stop forwarding webhooks for an Embedded Signup account.

	Parameters:
	        account (str, required): The WhatsApp Account name.

	Returns:
	        None
	"""
	doc = frappe.get_doc("WhatsApp Account", account)
	if not doc.hub_connection:
		frappe.throw(_("The account was not connected through the hub"))
	secret = doc.get_password("app_secret")
	call_hub(
		"disconnect",
		{"connection": doc.hub_connection, "signature": sign_disconnect(doc.hub_connection, secret)},
	)
	doc.db_set({"enabled": 0, "hub_connection": None})


def sign_disconnect(connection: str, secret: str) -> str:
	"""
	Return the proof that this site may disconnect a hub connection.

	Parameters:
	        connection (str, required): The hub connection name.
	        secret (str, required): The forwarding secret of the connection.

	Returns:
	        str: Hex HMAC-SHA256 of "disconnect:<connection>".
	"""
	return hmac.new(secret.encode(), f"disconnect:{connection}".encode(), hashlib.sha256).hexdigest()


def call_hub(method: str, payload: dict) -> dict:
	"""
	Call a hub API method and return its data, or raise the hub's error message.

	Parameters:
	        method (str, required): "start", "claim" or "disconnect".
	        payload (dict, required): The JSON body.

	Returns:
	        dict: The "data" of the hub's answer.
	"""
	hub_url = (frappe.db.get_single_value("WhatsApp Settings", "hub_url") or "").rstrip("/")
	if not hub_url:
		frappe.throw(_("Set the Hub URL in WhatsApp Settings first"))
	try:
		response = requests.post(hub_url + HUB_API + method, json=payload, timeout=TIMEOUT_SECONDS)
	except requests.RequestException as exc:
		frappe.throw(_("Could not reach the WhatsApp hub {0}: {1}").format(hub_url, str(exc)))
	answer = __decode(response)
	envelope = answer.get("message") if isinstance(answer.get("message"), dict) else {}
	if not response.ok or not envelope.get("status"):
		frappe.throw(_("The WhatsApp hub refused the request: {0}").format(__error_text(answer)))
	return envelope.get("data") or {}


def __decode(response) -> dict:
	"""
	Decode the hub's JSON answer.

	Parameters:
	        response (requests.Response, required): The HTTP response.

	Returns:
	        dict: The answer, or {"exception": text} when it is not JSON.
	"""
	try:
		return response.json()
	except ValueError:
		return {"exception": response.text[:500]}


def __error_text(answer: dict) -> str:
	"""
	Find the readable error in a Frappe error answer.

	Parameters:
	        answer (dict, required): The decoded answer.

	Returns:
	        str: The first server message, or the exception text.
	"""
	try:
		messages = json.loads(answer.get("_server_messages") or "[]")
		return json.loads(messages[0]).get("message") if messages else answer.get("exception", "")
	except (ValueError, TypeError, AttributeError):
		return str(answer.get("exception") or answer)
