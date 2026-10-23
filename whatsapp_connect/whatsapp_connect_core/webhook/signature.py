# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Check that a webhook call was signed by Meta (X-Hub-Signature-256)."""

import hashlib
import hmac

import frappe
from frappe.utils.password import get_decrypted_password

SIGNATURE_HEADER = "X-Hub-Signature-256"
PREFIX = "sha256="


def is_signed_by_meta(raw_body: bytes, signature_header: str | None) -> bool:
	"""
	Tell if the request may be processed.

	With an App Secret on any enabled account, the signature must match one of
	the secrets. Without one, the request is accepted unless WhatsApp Settings
	says to refuse unsigned calls.

	Parameters:
	        raw_body (bytes, required): The exact request body.
	        signature_header (str, optional): Value of the X-Hub-Signature-256 header.

	Returns:
	        bool: True when the request may be processed.
	"""
	secrets = get_app_secrets()
	if not secrets:
		return not frappe.db.get_single_value("WhatsApp Settings", "require_signed_webhooks")
	return signature_matches(raw_body, signature_header, secrets)


def signature_matches(raw_body: bytes, signature_header: str | None, secrets: list[str]) -> bool:
	"""
	Compare the header with the HMAC-SHA256 of the body for each secret, in constant time.

	Parameters:
	        raw_body (bytes, required): The exact request body.
	        signature_header (str, optional): "sha256=<hex>".
	        secrets (list[str], required): App Secrets to try.

	Returns:
	        bool: True when one secret produces the same signature.
	"""
	if not signature_header or not signature_header.startswith(PREFIX):
		return False
	received = signature_header[len(PREFIX) :].strip().lower()
	return any(
		hmac.compare_digest(received, hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest())
		for secret in secrets
	)


def get_app_secrets() -> list[str]:
	"""
	Return the App Secrets of all enabled WhatsApp Accounts.

	Returns:
	        list[str]: The secrets that are set.
	"""
	secrets = []
	for account in frappe.get_all("WhatsApp Account", filters={"enabled": 1}, pluck="name"):
		secret = get_decrypted_password("WhatsApp Account", account, "app_secret", raise_exception=False)
		if secret:
			secrets.append(secret)
	return secrets
