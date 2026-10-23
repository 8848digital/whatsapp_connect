# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Fake Meta answers for the setup tests."""

from urllib.parse import urlparse

import frappe
from frappe.utils.password import set_encrypted_password

from whatsapp_connect.tests.utils import graph_response

HUB_APP_SECRET = "hub-app-secret"


class FakeGraph:
	"""Answers Graph API calls by path; keeps the calls for assertions."""

	def __init__(self, app_id: str, waba_id: str, phone_number_id: str, expires_at: int = 0):
		"""Answers for one app, business account and phone number."""
		self.calls = []
		self.answers = {
			("GET", "debug_token"): {
				"data": {
					"is_valid": True,
					"app_id": app_id,
					"expires_at": expires_at,
					"scopes": ["whatsapp_business_management", "whatsapp_business_messaging"],
					"granular_scopes": [{"scope": "whatsapp_business_management", "target_ids": [waba_id]}],
				}
			},
			("GET", waba_id): {"id": waba_id, "name": "Asha Traders"},
			("GET", f"{waba_id}/phone_numbers"): {
				"data": [
					{
						"id": phone_number_id,
						"display_phone_number": "+91 98765 43210",
						"verified_name": "Asha Traders",
					}
				]
			},
			("GET", phone_number_id): {
				"display_phone_number": "+91 98765 43210",
				"verified_name": "Asha Traders",
				"quality_rating": "GREEN",
			},
			("GET", f"{waba_id}/message_templates"): {"data": []},
		}

	def __call__(self, method, url, **kwargs):
		"""Return the answer for the path, or {"success": true}."""
		path = urlparse(url).path.split("/", 2)[2]
		self.calls.append((method, path, kwargs))
		return graph_response(self.answers.get((method, path), {"success": True, "id": "x"}))

	def paths(self, method: str = "POST") -> list[str]:
		"""The paths called with a method."""
		return [path for called, path, _ in self.calls if called == method]


def enable_hub(**values) -> None:
	"""Turn this test site into a hub with a fake Meta app."""
	settings = frappe.get_doc("WhatsApp Hub Settings")
	settings.update(
		{
			"enabled": 1,
			"allow_insecure_sites": 1,
			"app_id": "hub-app",
			"config_id": "config-1",
			"verify_token": "hub-verify",
			**values,
		}
	)
	settings.save(ignore_permissions=True)
	set_encrypted_password(
		"WhatsApp Hub Settings", "WhatsApp Hub Settings", HUB_APP_SECRET, "app_secret"
	)
