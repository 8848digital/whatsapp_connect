# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from werkzeug.wrappers import Response

import frappe

from whatsapp_connect.whatsapp_connect_core.webhook import handler
from whatsapp_connect.whatsapp_connect_core.webhook.signature import SIGNATURE_HEADER


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method -- Meta calls the webhook without a session; POST is checked with X-Hub-Signature-256 and GET with the verify token
@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def receive():
	"""
	Webhook for the Meta WhatsApp Cloud API. Set this URL as the callback URL in
	the Meta App Dashboard. GET answers the subscription handshake; POST receives
	messages, statuses and other events, signed with the App Secret.

	**Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.webhook.receive`
	**HTTP Method:** GET, POST
	**Parameters:**
	        - hub.mode (str, required for GET): "subscribe"
	        - hub.verify_token (str, required for GET): The Webhook Verify Token of a WhatsApp Account
	        - hub.challenge (str, required for GET): Value to echo back
	        - body (JSON, required for POST): Meta's webhook payload
	        - X-Hub-Signature-256 (header, required for POST when an App Secret is set)
	**Response:**
	Plain text, as Meta expects: the challenge for GET; "OK" for POST (200).
	403 when the verify token or the signature does not match.
	"""
	if frappe.request.method == "GET":
		return handler.verify_subscription(frappe.request.args)
	return handler.receive(
		frappe.request.get_data(cache=True), frappe.request.headers.get(SIGNATURE_HEADER)
	)
