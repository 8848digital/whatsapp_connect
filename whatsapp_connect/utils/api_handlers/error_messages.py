# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""
Error Message Cleanup Helpers
Extracts and sanitizes error messages from raw Frappe error responses so
that no traceback, DB driver text, or bare exception class path is ever
surfaced to a client. Used by response_formatter.py's format_error_response.

Location: apps/whatsapp_connect/whatsapp_connect/utils/api_handlers/error_messages.py
Shared, non-whitelisted helper — lives in utils/api_handlers/ per the
frappe-app-dev skill's API convention.
"""

import json
import re
from typing import Dict, Optional

# Strips a leading "package.module.ExceptionClass: " prefix off a raw
# exception repr, e.g. "frappe.exceptions.DuplicateEntryError: (...)".
EXCEPTION_PREFIX_RE = re.compile(r"^[\w\.]+(?:Error|Exception):\s*")

# Maps Frappe exception type names to the HTTP codes in the 8848 standard.
# NOTE: 422 (Business Rule Validation Failed) has no dedicated Frappe
# exception class — raise it explicitly via api_response()/frappe.throw
# with a custom exception in your API method rather than relying on this
# generic mapping, or it will fall through to 400/500.
EXCEPTION_STATUS_MAP = {
	"PermissionError": 403,
	"ValidationError": 400,
	"DoesNotExistError": 404,
	"DuplicateEntryError": 409,
	"AuthenticationError": 401,
	"LinkValidationError": 400,
	"MandatoryError": 400,
}

# Default, human-readable messages per status code — used whenever the raw
# exception text can't be safely cleaned into something user-facing.
DEFAULT_MESSAGES = {
	400: "Validation failed",
	401: "Invalid authentication token",
	403: "You do not have permission to perform this action",
	404: "The requested record was not found",
	409: "Duplicate record found",
	422: "Business rule validation failed",
	429: "Too many requests, please try again later",
	500: "Internal server error",
}


def extract_raw_error_message(response_data: Dict) -> str:
	"""
	Pull the best available raw error message out of a Frappe error body.
	Prefers server messages (already human-facing) over the raw exception
	repr, which frequently contains tracebacks/DB error text.

	Parameters:
		response_data (dict, required): Parsed JSON body of the original Frappe response.

	Returns:
		str: Best-effort raw error message string.
	"""
	if "_server_messages" in response_data:
		try:
			messages = json.loads(response_data["_server_messages"])
			if messages:
				first_message = json.loads(messages[0])
				msg = first_message.get("message")
				if msg:
					return msg
		except Exception:
			pass

	if "_error_message" in response_data:
		return response_data["_error_message"]

	if "exception" in response_data:
		return response_data["exception"]

	if "message" in response_data:
		return response_data["message"]

	return "An error occurred"


def clean_duplicate_entry_message(raw: str) -> Optional[str]:
	"""
	Turn a raw DuplicateEntryError repr, e.g.
	"frappe.exceptions.DuplicateEntryError: ('Sales Partner', 'Guion', ...)",
	into a friendly sentence like "Sales Partner 'Guion' already exists".

	Parameters:
		raw (str, required): Raw exception message/repr.

	Returns:
		str or None: Friendly message, or None if the expected pattern isn't found.
	"""
	match = re.search(r"\(\s*'([^']+)'\s*,\s*'([^']+)'", raw)
	if match:
		doctype, name = match.group(1), match.group(2)
		return f"{doctype} '{name}' already exists"
	return None


def is_safe_to_show(cleaned_raw: str) -> bool:
	"""
	Decide whether a cleaned raw error string looks like an actual sentence
	meant for humans — not a bare dotted class path (e.g.
	"frappe.exceptions.AuthenticationError") and not traceback/DB noise.

	Parameters:
		cleaned_raw (str, required): Error text after prefix stripping.

	Returns:
		bool: True if safe to show directly to a client as `message`.
	"""
	is_bare_class_path = bool(re.match(r"^[\w\.]+$", cleaned_raw))
	return (
		bool(cleaned_raw)
		and len(cleaned_raw) < 150
		and not is_bare_class_path
		and not re.search(r"IntegrityError|Traceback|line \d+, in |File \"", cleaned_raw)
	)