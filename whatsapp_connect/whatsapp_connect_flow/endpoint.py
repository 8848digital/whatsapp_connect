# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""The Flow data endpoint: Meta calls it, encrypted, when a flow with an endpoint moves on.

A flow can answer with its own logic through the "whatsapp_connect_flow_handlers"
hook, for example {"Book a visit": "my_app.flows.book_a_visit"}: the function gets
(request, flow) and returns the answer object. Without one, the customer goes to
the next screen, and the last screen completes the flow.
"""

import json

from werkzeug.wrappers import Response

import frappe
from frappe.utils.password import get_decrypted_password

from whatsapp_connect.whatsapp_connect_core.webhook.signature import is_signed_by_meta
from whatsapp_connect.whatsapp_connect_flow.crypto import (
	FlowDecryptionError,
	decrypt_request,
	encrypt_response,
)
from whatsapp_connect.whatsapp_connect_flow.responses import find_flow_by_token

# Meta asks for 421 when a request cannot be decrypted, so it refreshes the public key.
DECRYPTION_FAILED = 421


def handle_request(raw_body: bytes, signature_header: str | None) -> Response:
	"""
	Check, decrypt, answer and encrypt one Flow endpoint request.

	Parameters:
	        raw_body (bytes, required): The exact request body.
	        signature_header (str, optional): The X-Hub-Signature-256 header.

	Returns:
	        Response: The encrypted answer as plain text; 403, 400 or 421 on errors.
	"""
	if not is_signed_by_meta(raw_body, signature_header):
		return Response("Invalid signature", status=403, mimetype="text/plain")
	try:
		body = json.loads(raw_body or b"{}")
	except ValueError:
		return Response("Invalid JSON", status=400, mimetype="text/plain")

	decrypted = __decrypt(body)
	if not decrypted:
		return Response("Decryption failed", status=DECRYPTION_FAILED, mimetype="text/plain")
	request, aes_key, iv = decrypted
	answer = build_answer(request)
	return Response(encrypt_response(answer, aes_key, iv), status=200, mimetype="text/plain")


def build_answer(request: dict) -> dict:
	"""
	Answer a decrypted request: health check, error notice, custom handler, or the default.

	Parameters:
	        request (dict, required): The decrypted request (action, screen, data, flow_token).

	Returns:
	        dict: The answer object.
	"""
	if request.get("action") == "ping":
		return {"data": {"status": "active"}}
	if (request.get("data") or {}).get("error"):
		return {"data": {"acknowledged": True}}

	flow = find_flow_by_token(request.get("flow_token"))
	handler = (
		frappe.get_hooks("whatsapp_connect_flow_handlers", default={}).get(flow) if flow else None
	)
	if handler:
		return frappe.get_attr(handler[-1])(request, flow)
	return __default_answer(request, flow)


def __default_answer(request: dict, flow: str | None) -> dict:
	"""
	Go to the first screen on INIT, to the next screen on data_exchange; finish after the last.

	Parameters:
	        request (dict, required): The decrypted request.
	        flow (str, optional): The WhatsApp Flow name.

	Returns:
	        dict: The answer object.
	"""
	screens = (
		[row.screen_id for row in frappe.get_cached_doc("WhatsApp Flow", flow).screens] if flow else []
	)
	data = request.get("data") or {}
	current = request.get("screen")
	if request.get("action") == "INIT" or current not in screens:
		return {"screen": screens[0] if screens else "SUCCESS", "data": {}}
	if request.get("action") == "BACK":
		return {"screen": current, "data": {}}
	index = screens.index(current)
	if index + 1 < len(screens):
		return {"screen": screens[index + 1], "data": data}
	params = {"flow_token": request.get("flow_token"), **data}
	return {"screen": "SUCCESS", "data": {"extension_message_response": {"params": params}}}


def __decrypt(body: dict):
	"""
	Try the Flow key of each enabled account; Meta does not say which number the call is for.

	Parameters:
	        body (dict, required): The encrypted request body.

	Returns:
	        tuple | None: (request, aes_key, iv), or None when no key can decrypt it.
	"""
	for account in frappe.get_all("WhatsApp Account", filters={"enabled": 1}, pluck="name"):
		private_key = get_decrypted_password(
			"WhatsApp Account", account, "flow_private_key", raise_exception=False
		)
		if not private_key:
			continue
		try:
			return decrypt_request(body, private_key)
		except FlowDecryptionError:
			continue
	return None
