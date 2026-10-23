# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""
Response Envelope Builder
Core builder for the 8848 Digital API Response Standard envelope:

	{
	    "status": true,
	    "status_code": 200,
	    "message": "Data fetched successfully",
	    "data": {},
	    "errors": null
	}

Location: apps/whatsapp_connect/whatsapp_connect/utils/api_handlers/envelope.py
Shared, non-whitelisted helper — lives in utils/api_handlers/ per the
frappe-app-dev skill's API convention, imported by response_formatter.py
and by any `<module_name>/api/vN/` file that calls api_response() directly.
"""

from typing import Any, Dict, Optional


def get_custom_response_format(
	status: bool = True,
	status_code: int = 200,
	message: str = "",
	data: Any = None,
	errors: Optional[Any] = None,
) -> Dict:
	"""
	Build the standard response envelope.

	All five fields are always present, per the 8848 Digital API Response
	Standard (data/errors may be null, but the keys are never stripped).

	Parameters:
		status (bool, optional): True for success, False for failure. Default True.
		status_code (int, optional): HTTP status code, mirrored in the response body. Default 200.
		message (str, optional): Human-readable, user-facing message.
		data (object/array/None, optional): Response payload.
		errors (object/array/None, optional): Error details.

	Returns:
		dict: Standard response dictionary
		`{"status", "status_code", "message", "data", "errors"}`.
	"""
	return {
		"status": status,
		"status_code": status_code,
		"message": message,
		"data": data,
		"errors": errors,
	}


def is_already_formatted(value: Any) -> bool:
	"""
	Check whether a dict already matches the standard envelope, to avoid
	double-wrapping.

	Parameters:
		value (Any, required): Candidate value to check.

	Returns:
		bool: True if value already has the standard status/status_code keys.
	"""
	return isinstance(value, dict) and "status" in value and "status_code" in value


def api_response(
	status: bool = True,
	code: int = 200,
	message: str = "",
	data: Any = None,
	errors: Optional[Any] = None,
):
	"""
	Build the standard API response envelope used across all whitelisted
	endpoints in this app, regardless of which module they belong to. Call
	this directly from a thin `<module_name>/api/` wrapper — see api.md.

	Usage:
		from whatsapp_connect.utils.api_handlers.response_formatter import api_response

		@frappe.whitelist()
		def get_customer(customer: str):
			return api_response(
				status=True,
				code=200,
				message="Customer details fetched successfully",
				data=customer_data,
			)

		# Business rule failure (no dedicated Frappe exception class exists
		# for this, so build it explicitly):
		return api_response(
			status=False,
			code=422,
			message="Insufficient stock available",
			errors={"item_code": item_code},
		)

	Parameters:
		status (bool, optional): True for success, False for failure. Default True.
		code (int, optional): HTTP status code, mirrored in the response body. Default 200.
		message (str, optional): Human-readable, user-facing message.
		data (object/array/None, optional): Response payload.
		errors (object/array/None, optional): Error details, if any.

	Returns:
		dict: Standard response dictionary
		`{"status", "status_code", "message", "data", "errors"}`.
	"""
	return get_custom_response_format(
		status=status, status_code=code, message=message, data=data, errors=errors
	)