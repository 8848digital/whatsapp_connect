# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""The hub forwards Meta's calls to the sites that connected through it.

Meta signs its calls with the hub app's secret, which sites must not know.
The hub checks that signature and signs the forwarded call with the site's
own forwarding secret, which the site keeps as its App Secret.
"""

import hashlib
import hmac
import json
import time

import requests
from werkzeug.wrappers import Response

import frappe
from frappe.utils import cint, now_datetime

from whatsapp_connect.whatsapp_connect_core.webhook.signature import (
	SIGNATURE_HEADER,
	signature_matches,
)
from whatsapp_connect.whatsapp_connect_setup.hub.settings import get_app_secret, get_hub_settings

DOCTYPE = "WhatsApp Hub Connection"
ATTEMPTS = 3
WEBHOOK_TIMEOUT_SECONDS = 15
# Meta waits about 10 seconds for a Flow endpoint answer.
FLOW_TIMEOUT_SECONDS = 9


def verify_subscription(query: dict) -> Response:
	"""
	Answer Meta's GET handshake for the hub app's webhook.

	Parameters:
	        query (dict, required): hub.mode, hub.verify_token and hub.challenge.

	Returns:
	        Response: The challenge (200), or 403.
	"""
	token = get_hub_settings().verify_token
	if query.get("hub.mode") == "subscribe" and token and query.get("hub.verify_token") == token:
		return Response(query.get("hub.challenge") or "", status=200, mimetype="text/plain")
	return Response("Verify token does not match", status=403, mimetype="text/plain")


def receive_webhook(raw_body: bytes, signature_header: str | None) -> Response:
	"""
	Check Meta's signature and queue one forward per entry and connected site.

	Parameters:
	        raw_body (bytes, required): The exact request body.
	        signature_header (str, optional): The X-Hub-Signature-256 header.

	Returns:
	        Response: 200 when accepted, 403 for a bad signature, 400 for bad JSON.
	"""
	if not signature_matches(raw_body, signature_header, [get_app_secret()]):
		return Response(f"Invalid or missing {SIGNATURE_HEADER}", status=403, mimetype="text/plain")
	try:
		data = json.loads(raw_body or b"{}")
	except ValueError:
		return Response("Invalid JSON", status=400, mimetype="text/plain")
	for entry in data.get("entry") or []:
		filters = {"waba_id": str(entry.get("id") or ""), "status": "Claimed"}
		body = json.dumps({"object": data.get("object"), "entry": [entry]})
		for connection in frappe.get_all(DOCTYPE, filters=filters, pluck="name"):
			frappe.enqueue(forward_webhook, queue="short", connection=connection, body=body)
	return Response("OK", status=200, mimetype="text/plain")


def forward_webhook(connection: str, body: str) -> None:
	"""
	Post a webhook to the site, signed with its forwarding secret, with retries.

	Parameters:
	        connection (str, required): The WhatsApp Hub Connection name.
	        body (str, required): The JSON body to forward.

	Returns:
	        None
	"""
	doc = frappe.get_doc(DOCTYPE, connection)
	headers = __signed_headers(doc, body.encode(), "application/json")
	error = None
	for attempt in range(ATTEMPTS):
		try:
			response = requests.post(
				doc.callback_url, data=body.encode(), headers=headers, timeout=WEBHOOK_TIMEOUT_SECONDS
			)
			if response.ok:
				doc.db_set("last_forwarded_on", now_datetime(), update_modified=False)
				return
			error = f"HTTP {response.status_code}: {response.text[:300]}"
		except requests.RequestException as exc:
			error = str(exc)
		if attempt < ATTEMPTS - 1:
			time.sleep(2**attempt)
	doc.db_set(
		{"failed_forwards": cint(doc.failed_forwards) + 1, "last_error": error},
		update_modified=False,
	)


def proxy_flow_request(connection: str, raw_body: bytes, signature_header: str | None) -> Response:
	"""
	Pass a Flow endpoint call to the site and return the site's answer to Meta.

	The body stays encrypted with the site's Flow key; the hub cannot read it.

	Parameters:
	        connection (str, required): The WhatsApp Hub Connection name (from the URL).
	        raw_body (bytes, required): The exact request body.
	        signature_header (str, optional): The X-Hub-Signature-256 header.

	Returns:
	        Response: The site's answer, 403 for a bad signature, 404 for an unknown connection.
	"""
	if not signature_matches(raw_body, signature_header, [get_app_secret()]):
		return Response("Invalid signature", status=403, mimetype="text/plain")
	name = frappe.db.get_value(DOCTYPE, {"name": connection or "", "status": "Claimed"})
	if not name:
		return Response("Unknown connection", status=404, mimetype="text/plain")
	doc = frappe.get_doc(DOCTYPE, name)
	try:
		response = requests.post(
			doc.flow_url,
			data=raw_body,
			headers=__signed_headers(doc, raw_body, "application/json"),
			timeout=FLOW_TIMEOUT_SECONDS,
		)
	except requests.RequestException:
		return Response("The site did not answer", status=502, mimetype="text/plain")
	return Response(response.content, status=response.status_code, mimetype="text/plain")


def __signed_headers(doc, body: bytes, content_type: str) -> dict:
	"""
	Return the headers of a forwarded call, signed with the connection's secret.

	Parameters:
	        doc (Document, required): The WhatsApp Hub Connection.
	        body (bytes, required): The body that is sent.
	        content_type (str, required): The Content-Type.

	Returns:
	        dict: Content-Type and X-Hub-Signature-256.
	"""
	secret = doc.get_password("forward_secret")
	digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
	return {"Content-Type": content_type, SIGNATURE_HEADER: f"sha256={digest}"}
