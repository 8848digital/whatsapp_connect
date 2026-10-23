# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe

from whatsapp_connect.tests.utils import (
	REQUESTS,
	IntegrationTestCase,
	graph_response,
	make_account,
)
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_account.account_utils import (
	get_account_by_phone_number_id,
	get_default_account,
	subscribe_app,
)


class TestWhatsAppAccount(IntegrationTestCase):
	"""Defaults, settings cleanup and the webhook subscription."""

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_only_one_default_per_direction(self):
		first = make_account("Test Default A", default_outgoing=1)
		second = make_account("Test Default B")
		account = frappe.get_doc("WhatsApp Account", second)
		account.default_outgoing = 1
		account.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("WhatsApp Account", first, "default_outgoing"), 0)
		self.assertEqual(get_default_account("outgoing"), second)

	def test_version_and_url_are_cleaned(self):
		account = frappe.get_doc("WhatsApp Account", make_account("Test Clean"))
		account.graph_api_version = "21.0"
		account.graph_api_url = "https://graph.facebook.com/"
		account.save(ignore_permissions=True)
		self.assertEqual(
			(account.graph_api_version, account.graph_api_url), ("v21.0", "https://graph.facebook.com")
		)

	def test_account_by_phone_number_id(self):
		name = make_account("Test Lookup")
		phone_number_id = frappe.db.get_value("WhatsApp Account", name, "phone_number_id")
		self.assertEqual(get_account_by_phone_number_id(phone_number_id), name)
		frappe.db.set_value("WhatsApp Account", name, "enabled", 0)
		self.assertIsNone(get_account_by_phone_number_id(phone_number_id))

	def test_subscribe_app(self):
		name = make_account("Test Subscribe")
		with patch(REQUESTS, return_value=graph_response({"success": True})) as request:
			subscribe_app(name)
		waba = frappe.db.get_value("WhatsApp Account", name, "business_account_id")
		self.assertTrue(request.call_args.args[1].endswith(f"/{waba}/subscribed_apps"))

	def test_failed_subscription_raises(self):
		name = make_account("Test Subscribe Fail")
		with patch(REQUESTS, return_value=graph_response({"success": False})), self.assertRaises(
			frappe.ValidationError
		):
			subscribe_app(name)
