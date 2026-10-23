# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Hub endpoints. They answer only on a site with WhatsApp Hub Settings enabled."""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_core.webhook.signature import SIGNATURE_HEADER
from whatsapp_connect.whatsapp_connect_setup.hub import relay, signup


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method -- called by other sites' servers; rate limited, and the session only works with the claim secret
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def start(site_url: str, callback_url: str, flow_url: str, coexistence: int = 0):
	"""
	        Open an Embedded Signup session for a site. Called by the site's server.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub.start`
	        **HTTP Method:** POST
	        **Parameters:**
	                - site_url (str, required): The site's base URL (public, https)
	                - callback_url (str, required): The site's webhook URL
	                - flow_url (str, required): The site's Flow endpoint URL
	                - coexistence (int, optional): 1 when the number stays on the WhatsApp Business app
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Signup session opened",
	                        "data": {"session": "3f2a...", "claim_secret": "k9P...", "signup_url": "https://hub.example.com/whatsapp_signup?session=3f2a..."},
	                        "errors": null
	                }
	```
	"""
	data = signup.start(site_url, callback_url, flow_url, coexistence)
	return api_response(message=_("Signup session opened"), data=data)


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method -- called by the hub's signup page in the user's browser; needs the session and a code from Meta
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def finish(session: str, code: str, waba_id: str, phone_number_id: str, event: str):
	"""
	        Finish an Embedded Signup: exchange Meta's code and subscribe the hub app.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub.finish`
	        **HTTP Method:** POST
	        **Parameters:**
	                - session (str, required): The signup session
	                - code (str, required): The code from Meta's login popup
	                - waba_id (str, required): The chosen WhatsApp Business Account ID
	                - phone_number_id (str, required): The chosen phone number ID
	                - event (str, required): The popup's finish event, for example FINISH
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "WhatsApp is connected",
	                        "data": {"site_url": "https://erp.example.com", "display_phone_number": "+91 98765 43210"},
	                        "errors": null
	                }
	```
	"""
	data = signup.finish(session, code, waba_id, phone_number_id, event)
	return api_response(message=_("WhatsApp is connected"), data=data)


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method -- called by the site's server; needs the one-time claim secret
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def claim(session: str, claim_secret: str):
	"""
	        Give a site its business token and forwarding secret, once.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub.claim`
	        **HTTP Method:** POST
	        **Parameters:**
	                - session (str, required): The signup session
	                - claim_secret (str, required): The secret returned by start
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Connection claimed",
	                        "data": {"connection": "3f2a...", "access_token": "EAAG...", "forward_secret": "x8...", "waba_id": "1029", "phone_number_id": "1123"},
	                        "errors": null
	                }
	```
	"""
	return api_response(message=_("Connection claimed"), data=signup.claim(session, claim_secret))


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method -- called by the site's server; needs an HMAC made with the forwarding secret
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def disconnect(connection: str, signature: str):
	"""
	        Stop forwarding webhooks to a site.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub.disconnect`
	        **HTTP Method:** POST
	        **Parameters:**
	                - connection (str, required): The hub connection name
	                - signature (str, required): Hex HMAC-SHA256 of "disconnect:<connection>" with the forwarding secret
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Disconnected",
	                        "data": null,
	                        "errors": null
	                }
	```
	"""
	signup.disconnect(connection, signature)
	return api_response(message=_("Disconnected"))


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method -- Meta calls the hub webhook without a session; POST is checked with X-Hub-Signature-256 and GET with the verify token
@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def webhook():
	"""
	Webhook of the hub's Meta app. Set this URL as the callback URL of the hub
	app. Calls are checked and forwarded to the connected sites.

	**Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub.webhook`
	**HTTP Method:** GET, POST
	**Parameters:**
	        - hub.mode, hub.verify_token, hub.challenge (str, required for GET)
	        - body (JSON, required for POST): Meta's webhook payload
	        - X-Hub-Signature-256 (header, required for POST)
	**Response:**
	Plain text: the challenge for GET; "OK" for POST (200); 403 for a bad token or signature.
	"""
	if frappe.request.method == "GET":
		return relay.verify_subscription(frappe.request.args)
	return relay.receive_webhook(
		frappe.request.get_data(cache=True), frappe.request.headers.get(SIGNATURE_HEADER)
	)


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method -- Meta calls Flow endpoints without a session; checked with X-Hub-Signature-256, and the body stays encrypted for the site
@frappe.whitelist(allow_guest=True, methods=["POST"])
def flow_endpoint(connection: str):
	"""
	Flow data endpoint of hub connections: passes Meta's call to the site and returns its answer.

	**Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub.flow_endpoint?connection=<name>`
	**HTTP Method:** POST
	**Parameters:**
	        - connection (str, required): The hub connection name (query string)
	        - body (JSON, required): Meta's encrypted Flow request
	        - X-Hub-Signature-256 (header, required)
	**Response:**
	The site's answer (plain text, base64), 403 for a bad signature, 404 for an unknown connection.
	"""
	return relay.proxy_flow_request(
		connection, frappe.request.get_data(cache=True), frappe.request.headers.get(SIGNATURE_HEADER)
	)
