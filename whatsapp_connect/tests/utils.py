# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Shared test helpers: accounts, numbers, Graph API mocks and webhook calls."""

import hashlib
import hmac
import json
import random
from unittest.mock import MagicMock, patch

import frappe
from frappe.utils.password import set_encrypted_password

try:
	from frappe.tests import IntegrationTestCase
except ImportError:  # Frappe 14
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

# A minimal valid one-page PDF: Frappe 15+ parses uploaded PDFs.
MINIMAL_PDF = (
	b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
	b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
	b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 10 10]>>endobj\n"
	b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \n"
	b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n159\n%%EOF\n"
)
REQUESTS = "whatsapp_connect.whatsapp_connect_core.cloud_api.client.requests.request"
APP_SECRET = "test-app-secret"


def make_account(
	name: str = "Test WhatsApp Account", app_secret: str | None = None, **values
) -> str:
	"""
	Create (once) an enabled WhatsApp Account for tests and set its secrets.

	Parameters:
	        name (str, optional): Account name.
	        app_secret (str, optional): App Secret to set; None removes it.
	        **values: Other field values for a new account.

	Returns:
	        str: The WhatsApp Account name.
	"""
	if not frappe.db.exists("WhatsApp Account", name):
		suffix = frappe.generate_hash(length=8)
		frappe.get_doc(
			{
				"doctype": "WhatsApp Account",
				"account_name": name,
				"enabled": 1,
				"phone_number_id": f"phone-{suffix}",
				"business_account_id": f"waba-{suffix}",
				"verify_token": f"verify-{suffix}",
				"access_token": "test-token",
				**values,
			}
		).insert(ignore_permissions=True)
	set_encrypted_password("WhatsApp Account", name, "test-token", "access_token")
	if app_secret:
		set_encrypted_password("WhatsApp Account", name, app_secret, "app_secret")
	return name


def random_number() -> str:
	"""
	Return a unique test phone number, so rows from earlier runs never match.

	Returns:
	        str: A 12-digit number starting with 9199.
	"""
	return "9199" + "".join(random.choice("0123456789") for _ in range(8))


def graph_response(body: dict | None = None, status: int = 200) -> MagicMock:
	"""
	Build a fake requests.Response for the Graph API.

	Parameters:
	        body (dict, optional): The JSON answer.
	        status (int, optional): HTTP status. Default 200.

	Returns:
	        MagicMock: An object with ok, status_code, json() and text.
	"""
	response = MagicMock(ok=status < 400, status_code=status)
	response.json.return_value = body or {}
	response.text = json.dumps(body or {})
	return response


def sent(wamid: str = "wamid.TEST") -> MagicMock:
	"""
	Patch the Graph API so every call answers like a successful message send.

	Parameters:
	        wamid (str, optional): The message ID Meta returns.

	Returns:
	        MagicMock: The started patcher's mock (stop it with patch.stopall or a context manager).
	"""
	return patch(
		REQUESTS,
		return_value=graph_response({"messages": [{"id": wamid}], "id": "media-1", "success": True}),
	)


def sign(body: bytes, secret: str = APP_SECRET) -> str:
	"""
	Return the X-Hub-Signature-256 header value for a body.

	Parameters:
	        body (bytes, required): The request body.
	        secret (str, optional): The App Secret.

	Returns:
	        str: "sha256=<hex>".
	"""
	return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def webhook_body(account: str, field: str, value: dict) -> bytes:
	"""
	Build a webhook POST body for one change, with the account's phone number ID.

	Parameters:
	        account (str, required): The WhatsApp Account name.
	        field (str, required): The webhook field, for example "messages".
	        value (dict, required): The change value (metadata is added).

	Returns:
	        bytes: The JSON body.
	"""
	phone_number_id = frappe.db.get_value("WhatsApp Account", account, "phone_number_id")
	value = {
		"messaging_product": "whatsapp",
		"metadata": {"phone_number_id": phone_number_id},
		**value,
	}
	return json.dumps(
		{
			"object": "whatsapp_business_account",
			"entry": [{"changes": [{"field": field, "value": value}]}],
		}
	).encode()


def make_template(
	name: str = "test_order_update", account: str | None = None, status: str = "Approved", **values
) -> str:
	"""
	Create a WhatsApp Template directly in the database (Meta is not called).

	Parameters:
	        name (str, optional): Template name.
	        account (str, optional): WhatsApp Account; the default test account when None.
	        status (str, optional): Template status. Default "Approved".
	        **values: Other field values, for example buttons=[...].

	Returns:
	        str: The WhatsApp Template name ("<name>-en").
	"""
	template = frappe.get_doc(
		{
			"doctype": "WhatsApp Template",
			"template_name": name,
			"language_code": "en",
			"category": "UTILITY",
			"whatsapp_account": account or make_account(),
			"body": "Hello {{1}}, your order {{2}} is ready.",
			"body_samples": "Asha\nSO-0001",
			**values,
		}
	)
	if frappe.db.exists("WhatsApp Template", f"{name}-en"):
		frappe.delete_doc("WhatsApp Template", f"{name}-en", force=True, ignore_permissions=True)
	template.insert(ignore_permissions=True)
	template.db_set("status", status)
	return template.name
