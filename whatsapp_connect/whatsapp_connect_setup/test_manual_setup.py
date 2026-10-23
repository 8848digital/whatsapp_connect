# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe

from whatsapp_connect.tests.setup_fakes import FakeGraph
from whatsapp_connect.tests.utils import REQUESTS, IntegrationTestCase, graph_response
from whatsapp_connect.whatsapp_connect_setup.discovery import discover
from whatsapp_connect.whatsapp_connect_setup.manual_setup import connect_own_app

WEBHOOK_URL = (
	"https://erp.example.com/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.webhook.receive"
)


class TestManualSetup(IntegrationTestCase):
	"""Use my own Meta app: discovery, account, webhook and setup steps."""

	def setUp(self):
		"""Fresh IDs for one app, business account and number."""
		suffix = frappe.generate_hash(length=8)
		self.app_id, self.waba, self.phone = f"app-{suffix}", f"waba-{suffix}", f"phone-{suffix}"
		self.graph = FakeGraph(self.app_id, self.waba, self.phone)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def connect(self, register_number=0):
		"""Run connect_own_app with fake Meta answers and a public webhook URL."""
		with (
			patch(REQUESTS, side_effect=self.graph),
			patch(
				"whatsapp_connect.whatsapp_connect_setup.webhook_setup.webhook_url", return_value=WEBHOOK_URL
			),
			patch.object(frappe.db, "commit"),
		):
			return connect_own_app(self.app_id, "secret", "token-1", self.phone, register_number)

	def test_discover_lists_numbers_of_the_token(self):
		"""The business accounts come from the token's granular scopes."""
		with patch(REQUESTS, side_effect=self.graph):
			found = discover(self.app_id, "secret", "token-1")
		self.assertEqual(found["accounts"][0]["id"], self.waba)
		self.assertEqual(found["accounts"][0]["phone_numbers"][0]["id"], self.phone)

	def test_discover_refuses_a_token_of_another_app(self):
		"""A token of another app cannot be used with this App Secret."""
		self.graph.answers[("GET", "debug_token")]["data"]["app_id"] = "other-app"
		with patch(REQUESTS, side_effect=self.graph), self.assertRaises(frappe.ValidationError):
			discover(self.app_id, "secret", "token-1")

	def test_discover_refuses_an_invalid_token(self):
		"""Meta says the token is not valid."""
		with (
			patch(REQUESTS, return_value=graph_response({"data": {"is_valid": False}})),
			self.assertRaises(frappe.ValidationError),
		):
			discover(self.app_id, "secret", "token-1")

	def test_connect_saves_the_account_and_sets_the_webhook(self):
		"""The account is created and the app webhook points to this site."""
		result = self.connect()
		account = frappe.get_doc("WhatsApp Account", result["account"])
		self.assertEqual(account.phone_number_id, self.phone)
		self.assertEqual(account.business_account_id, self.waba)
		self.assertEqual(account.setup_method, "Manual")
		self.assertEqual(account.get_password("access_token"), "token-1")
		self.assertTrue(account.verify_token)
		self.assertIn(f"{self.app_id}/subscriptions", self.graph.paths())
		self.assertIn(f"{self.waba}/subscribed_apps", self.graph.paths())
		subscription = next(c for c in self.graph.calls if c[1] == f"{self.app_id}/subscriptions")
		self.assertEqual(subscription[2]["data"]["callback_url"], WEBHOOK_URL)
		self.assertEqual(subscription[2]["data"]["verify_token"], account.verify_token)
		failed = [step for step in result["steps"] if not step["ok"]]
		self.assertEqual(failed, [], failed)

	def test_connect_does_not_register_unless_asked(self):
		"""Registering a number that already sends messages could change its PIN."""
		self.connect()
		self.assertNotIn(f"{self.phone}/register", self.graph.paths())

	def test_register_saves_a_pin_and_keeps_it_out_of_the_log(self):
		"""A new 6-digit PIN is sent to Meta, saved encrypted and not logged."""
		result = self.connect(register_number=1)
		self.assertIn(f"{self.phone}/register", self.graph.paths())
		pin = frappe.get_doc("WhatsApp Account", result["account"]).get_password("registration_pin")
		self.assertRegex(pin, r"^\d{6}$")
		logged = frappe.get_all(
			"WhatsApp Log", filters={"endpoint": f"POST {self.phone}/register"}, pluck="request"
		)
		self.assertTrue(logged)
		self.assertFalse(any(pin in (request or "") for request in logged))

	def test_running_again_updates_the_same_account(self):
		"""Connecting the same number twice keeps one account."""
		first = self.connect()["account"]
		second = self.connect()["account"]
		self.assertEqual(first, second)
