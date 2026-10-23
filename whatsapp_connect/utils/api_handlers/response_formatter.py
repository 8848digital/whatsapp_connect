# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""
Custom Response Formatter for Custom App API
Transforms all Frappe API responses (including errors) into the
8848 Digital API Response Standard format:

	{
	    "status": true,
	    "status_code": 200,
	    "message": "Data fetched successfully",
	    "data": {},
	    "errors": null
	}

Location: apps/whatsapp_connect/whatsapp_connect/utils/api_handlers/response_formatter.py
This is a shared, non-whitelisted helper — per the frappe-app-dev skill's
API convention, it lives in utils/api_handlers/ at the app root, not inside
any module's api/ folder, and is reused by every module's api/vN/ files.

Split across three files to stay under the max-lines rule:
	envelope.py         — envelope builder, api_response() (re-exported below)
	error_messages.py   — exception message cleanup/mapping helpers
	response_formatter.py (this file) — after_request hook + formatters

Wired in hooks.py:
	after_request = ["whatsapp_connect.utils.api_handlers.response_formatter.format_frappe_response_to_custom"]
"""

import json
from typing import Dict

import frappe

from .envelope import api_response, get_custom_response_format, is_already_formatted
from .error_messages import (
	DEFAULT_MESSAGES,
	EXCEPTION_PREFIX_RE,
	EXCEPTION_STATUS_MAP,
	clean_duplicate_entry_message,
	extract_raw_error_message,
	is_safe_to_show,
)

# Re-exported so existing imports of
# `whatsapp_connect.utils.api_handlers.response_formatter.api_response` (and
# `get_custom_response_format`) keep working after the split.
__all__ = [
	"api_response",
	"get_custom_response_format",
	"format_frappe_response_to_custom",
	"format_success_response",
	"format_error_response",
]


def format_frappe_response_to_custom(request, response):
	"""
	after_request hook: rewrites Frappe's native response body into the
	standard envelope for both success and error responses, and aligns
	the actual HTTP status code with the mapped status_code.

	Parameters:
		request (Request, required): The current Werkzeug request object, passed by Frappe.
		response (Response, required): The current Werkzeug response object, passed by Frappe.

	Returns:
		None
	"""
	# Only touch whatsapp_connect API responses.
	if not request.path.startswith("/api/method/whatsapp_connect"):
		return

	if not response or not hasattr(response, "data"):
		return

	try:
		response_data = json.loads(response.data.decode("utf-8"))

		# Already formatted at the top level — leave as is.
		if is_already_formatted(response_data):
			return

		# Already formatted but nested under data/message — hoist it up.
		data_or_message = response_data.get("data") or response_data.get("message")
		if is_already_formatted(data_or_message):
			response.data = json.dumps(data_or_message, separators=(",", ":"))
			response.status_code = data_or_message["status_code"]
			return

		is_error = response.status_code >= 400

		if is_error:
			custom_response = format_error_response(response_data, response.status_code)
		else:
			custom_response = format_success_response(response_data, response.status_code)

		# Keep the real HTTP status code in sync with the body's status_code,
		# per the standard's "match HTTP status code with response body" rule.
		response.status_code = custom_response["status_code"]
		response.data = json.dumps(custom_response, separators=(",", ":"))

	except Exception as e:
		frappe.log_error(
			title="Response Formatting Error", message=f"Failed to format response: {str(e)}"
		)


def format_success_response(response_data: Dict, status_code: int = 200) -> Dict:
	"""
	Format a successful Frappe response body into the standard envelope.

	Parameters:
		response_data (dict, required): Parsed JSON body of the original Frappe response.
		status_code (int, optional): HTTP status code of the original response. Default 200.

	Returns:
		dict: Standard success response dictionary.
	"""
	data = response_data.get("data") or response_data.get("message")

	if is_already_formatted(data):
		return data

	message = None
	if "_server_messages" in response_data:
		try:
			messages = json.loads(response_data["_server_messages"])
			if messages:
				first_message = json.loads(messages[0])
				message = first_message.get("message")
		except Exception:
			pass

	return get_custom_response_format(
		status=True,
		status_code=status_code,
		message=message or "Request processed successfully",
		data=data,
		errors=None,
	)


def format_error_response(response_data: Dict, status_code: int) -> Dict:
	"""
	Format an error Frappe response body into the standard envelope.
	Raw exception text (tracebacks, DB driver errors) is never surfaced
	directly in `message` — only cleaned/friendly text is, with technical
	detail moved to `errors`.

	Parameters:
		response_data (dict, required): Parsed JSON body of the original Frappe response.
		status_code (int, required): HTTP status code of the original response.

	Returns:
		dict: Standard error response dictionary.
	"""
	error_type = response_data.get("exc_type", "Error")
	raw_message = extract_raw_error_message(response_data)
	cleaned_raw = EXCEPTION_PREFIX_RE.sub("", raw_message).strip()

	final_status_code = EXCEPTION_STATUS_MAP.get(error_type, status_code)

	# Try a friendly, exception-specific message first.
	error_message = None
	if error_type == "DuplicateEntryError":
		error_message = clean_duplicate_entry_message(raw_message)

	# 401/403 rarely carry any useful custom text from Frappe (often just
	# the bare exception class path) — always use the standard's exact
	# wording for these rather than risk leaking internals.
	if error_message is None and final_status_code in (401, 403):
		error_message = DEFAULT_MESSAGES[final_status_code]

	# Fall back to the cleaned raw text only if it looks safe to show;
	# otherwise use the generic per-status default.
	if error_message is None:
		error_message = (
			cleaned_raw
			if is_safe_to_show(cleaned_raw)
			else DEFAULT_MESSAGES.get(final_status_code, "An error occurred")
		)

	# NOTE: per 8848's docs, 401/403/404 default to errors=null (avoids
	# giving an attacker a token/permission/user-enumeration oracle). This
	# has been overridden on request to always populate `errors` with
	# technical detail for debugging, across all non-5xx error codes.
	errors = None
	if final_status_code < 500:
		errors = {"error": cleaned_raw or raw_message}
	else:
		# Never expose tracebacks to the client — log full detail server-side
		# under a reference id, return only that id.
		error_id = (
			f"ERR-{frappe.utils.now_datetime().strftime('%Y%m%d-%H%M%S')}-"
			f"{frappe.generate_hash(length=4).upper()}"
		)
		frappe.log_error(
			title=f"API Error [{error_id}]",
			message=f"Status code: {final_status_code}, Response: {response_data}",
		)
		errors = {"error_id": error_id}
		error_message = "Internal server error"

	return get_custom_response_format(
		status=False,
		status_code=final_status_code,
		message=error_message,
		data=None,
		errors=errors,
	)