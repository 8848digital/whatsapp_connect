# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""WhatsApp Log entries for Graph API calls."""

import json

import frappe


def log_request(account, method, path, request_body, http_status, answer, error) -> None:
	"""
	Save a Graph API call in WhatsApp Log. The access token is sent in a header,
	so it is never part of the logged request or response.

	Parameters:
	        account (str, required): The WhatsApp Account name.
	        method (str, required): HTTP method.
	        path (str, required): API path.
	        request_body (dict, optional): The body that was sent.
	        http_status (int, optional): HTTP status, None when the call failed.
	        answer (dict, optional): The decoded answer.
	        error (str, optional): Error text.

	Returns:
	        None
	"""
	frappe.get_doc(
		{
			"doctype": "WhatsApp Log",
			"log_type": "API Request",
			"whatsapp_account": account,
			"endpoint": f"{method} {path}",
			"success": int(bool(http_status and http_status < 400 and not error)),
			"http_status": http_status,
			"error": error,
			"request": json.dumps(request_body, default=str, indent=1) if request_body else None,
			"response": json.dumps(answer, default=str, indent=1) if answer else None,
		}
	).insert(ignore_permissions=True)
