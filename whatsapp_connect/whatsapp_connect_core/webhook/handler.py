# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Webhook entry point: the subscription handshake and the event router.

Each change in a webhook call has a "field". Core handles "messages" and
"smb_message_echoes"; other modules register their fields through the
"whatsapp_connect_webhook_fields" hook, for example
{"message_template_status_update": "whatsapp_connect...update_template_status"}.
"""

import json

from werkzeug.wrappers import Response

import frappe

from whatsapp_connect.whatsapp_connect_core.webhook.signature import (
	SIGNATURE_HEADER,
	is_signed_by_meta,
)

CORE_FIELDS = {
	"messages": "whatsapp_connect.whatsapp_connect_core.webhook.incoming.handle_messages_change",
	"smb_message_echoes": "whatsapp_connect.whatsapp_connect_core.webhook.echoes.handle_echoes_change",
}


def verify_subscription(query: dict) -> Response:
	"""
	Answer Meta's GET handshake with the challenge when the verify token is known.

	Parameters:
	        args (dict, required): Query arguments: hub.mode, hub.verify_token, hub.challenge.

	Returns:
	        Response: The challenge as plain text (200), or 403.
	"""
	token = query.get("hub.verify_token")
	known = token and frappe.db.exists("WhatsApp Account", {"verify_token": token, "enabled": 1})
	if query.get("hub.mode") == "subscribe" and known:
		return Response(query.get("hub.challenge") or "", status=200, mimetype="text/plain")
	return Response("Verify token does not match", status=403, mimetype="text/plain")


def receive(raw_body: bytes, signature_header: str | None) -> Response:
	"""
	Process a webhook POST: check the signature, log the call, and route each change.

	Parameters:
	        raw_body (bytes, required): The exact request body.
	        signature_header (str, optional): The X-Hub-Signature-256 header.

	Returns:
	        Response: 200 when processed, 403 for an unsigned or forged call, 400 for bad JSON.
	"""
	# Checked before anything is written, so forged calls cannot fill the database.
	if not is_signed_by_meta(raw_body, signature_header):
		return Response(f"Invalid or missing {SIGNATURE_HEADER}", status=403, mimetype="text/plain")
	try:
		data = json.loads(raw_body or b"{}")
	except ValueError:
		return Response("Invalid JSON", status=400, mimetype="text/plain")

	__log(data)
	handlers = {
		**CORE_FIELDS,
		**{
			field: paths[-1]
			for field, paths in frappe.get_hooks("whatsapp_connect_webhook_fields", default={}).items()
		},
	}
	for change in __changes(data):
		path = handlers.get(change.get("field"))
		if path:
			frappe.get_attr(path)(change.get("value") or {})
	return Response("OK", status=200, mimetype="text/plain")


def __changes(data: dict) -> list[dict]:
	"""
	Flatten the entries of a webhook call into one list of changes.

	Parameters:
	        data (dict, required): The decoded webhook body.

	Returns:
	        list[dict]: Change objects with "field" and "value".
	"""
	return [change for entry in data.get("entry") or [] for change in entry.get("changes") or []]


def __log(data: dict) -> None:
	"""
	Keep the webhook call in WhatsApp Log.

	Parameters:
	        data (dict, required): The decoded webhook body.

	Returns:
	        None
	"""
	fields = ", ".join(sorted({change.get("field") or "" for change in __changes(data)}))
	frappe.get_doc(
		{
			"doctype": "WhatsApp Log",
			"log_type": "Webhook",
			"endpoint": fields or "webhook",
			"success": 1,
			"request": json.dumps(data, indent=1),
		}
	).insert(ignore_permissions=True)
