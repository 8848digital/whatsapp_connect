# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Errors returned by the Graph API."""

import frappe

# Throughput and pair rate limits: the same request succeeds again a few seconds later.
RATE_LIMIT_CODES = {4, 80007, 130429, 131048, 131056}


class CloudAPIError(frappe.ValidationError):
	"""An error returned by the Graph API, with Meta's code and reason."""

	def __init__(
		self,
		message: str,
		code: int | None = None,
		details: str | None = None,
		http_status: int | None = None,
	):
		"""
		Keep Meta's error data next to the message.

		Parameters:
		        message (str, required): Meta's error message.
		        code (int, optional): Meta's error code, for example 131026.
		        details (str, optional): Meta's error details.
		        http_status (int, optional): HTTP status of the response.

		Returns:
		        None
		"""
		super().__init__(message)
		self.code = code
		self.details = details
		self.http_status = http_status

	@property
	def is_rate_limit(self) -> bool:
		"""
		Tell if Meta refused the request because of a rate limit.

		Returns:
		        bool: True for a rate-limit error, which can be retried later.
		"""
		return self.code in RATE_LIMIT_CODES

	def describe(self) -> str:
		"""
		Return Meta's message and details as one line, for error fields.

		Returns:
		        str: "message - details" or just the message.
		"""
		return " - ".join(part for part in (str(self), self.details) if part)
