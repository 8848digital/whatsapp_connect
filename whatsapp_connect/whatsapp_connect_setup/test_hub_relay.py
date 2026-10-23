# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import json
from unittest.mock import MagicMock, patch

import frappe

from whatsapp_connect.tests.setup_fakes import HUB_APP_SECRET, enable_hub
from whatsapp_connect.tests.utils import IntegrationTestCase, sign
from whatsapp_connect.whatsapp_connect_core.webhook.signature import signature_matches
from whatsapp_connect.whatsapp_connect_setup.hub import relay

RELAY = "whatsapp_connect.whatsapp_connect_setup.hub.relay"
SITE = "http://erp.example.com"


class TestHubRelay(IntegrationTestCase):
	"""The hub checks Meta's signature and forwards calls signed for each site."""

	def setUp(self):
		"""A hub with one claimed connection."""
		enable_hub()
		self.waba = f"waba-{frappe.generate_hash(length=8)}"
		self.connection = frappe.get_doc(
			{
				"doctype": "WhatsApp Hub Connection",
				"name": frappe.generate_hash(length=32),
				"status": "Claimed",
				"site_url": SITE,
				"callback_url": f"{SITE}/webhook",
				"flow_url": f"{SITE}/flow",
				"waba_id": self.waba,
				"forward_secret": "site-secret",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def body(self, waba=None) -> bytes:
		"""A webhook body for a business account."""
		entry = {"id": waba or self.waba, "changes": [{"field": "messages", "value": {}}]}
		return json.dumps({"object": "whatsapp_business_account", "entry": [entry]}).encode()

	def test_handshake_needs_the_hub_verify_token(self):
		"""Meta's GET handshake answers the challenge only with the right token."""
		query = {"hub.mode": "subscribe", "hub.verify_token": "hub-verify", "hub.challenge": "42"}
		self.assertEqual(relay.verify_subscription(query).get_data(as_text=True), "42")
		query["hub.verify_token"] = "wrong"
		self.assertEqual(relay.verify_subscription(query).status_code, 403)

	def test_webhook_is_queued_for_the_connected_site(self):
		"""A signed call is forwarded to the connection of the business account."""
		body = self.body()
		with patch(f"{RELAY}.frappe.enqueue") as enqueue:
			response = relay.receive_webhook(body, sign(body, HUB_APP_SECRET))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(enqueue.call_args.kwargs["connection"], self.connection.name)

	def test_unsigned_webhook_is_refused(self):
		"""A call signed with another secret is not forwarded."""
		body = self.body()
		with patch(f"{RELAY}.frappe.enqueue") as enqueue:
			response = relay.receive_webhook(body, sign(body, "not-the-hub-secret"))
		self.assertEqual(response.status_code, 403)
		enqueue.assert_not_called()

	def test_other_business_accounts_are_not_forwarded(self):
		"""Calls for an account that no site claimed go nowhere."""
		body = self.body(waba="waba-unknown")
		with patch(f"{RELAY}.frappe.enqueue") as enqueue:
			relay.receive_webhook(body, sign(body, HUB_APP_SECRET))
		enqueue.assert_not_called()

	def test_forward_signs_with_the_site_secret(self):
		"""The site can check the forwarded call with its own secret."""
		body = self.body().decode()
		with patch(f"{RELAY}.requests.post", return_value=MagicMock(ok=True)) as post:
			relay.forward_webhook(self.connection.name, body)
		headers = post.call_args.kwargs["headers"]
		self.assertTrue(
			signature_matches(body.encode(), headers["X-Hub-Signature-256"], ["site-secret"])
		)
		self.assertTrue(
			frappe.db.get_value("WhatsApp Hub Connection", self.connection.name, "last_forwarded_on")
		)

	def test_failed_forward_is_recorded(self):
		"""After the retries the error is kept on the connection."""
		with (
			patch(f"{RELAY}.requests.post", return_value=MagicMock(ok=False, status_code=500, text="down")),
			patch(f"{RELAY}.time.sleep"),
		):
			relay.forward_webhook(self.connection.name, self.body().decode())
		values = frappe.db.get_value(
			"WhatsApp Hub Connection", self.connection.name, ["failed_forwards", "last_error"], as_dict=True
		)
		self.assertEqual(values.failed_forwards, 1)
		self.assertIn("500", values.last_error)

	def test_flow_call_returns_the_site_answer(self):
		"""The encrypted Flow call goes to the site, and its answer back to Meta."""
		body = b'{"encrypted_flow_data": "x"}'
		answer = MagicMock(content=b"c2l0ZQ==", status_code=200)
		with patch(f"{RELAY}.requests.post", return_value=answer) as post:
			response = relay.proxy_flow_request(self.connection.name, body, sign(body, HUB_APP_SECRET))
		self.assertEqual(response.get_data(), b"c2l0ZQ==")
		self.assertEqual(post.call_args.args[0], f"{SITE}/flow")

	def test_flow_call_for_an_unknown_connection(self):
		"""Unknown or disconnected connections get 404."""
		body = b"{}"
		self.connection.db_set("status", "Disconnected")
		response = relay.proxy_flow_request(self.connection.name, body, sign(body, HUB_APP_SECRET))
		self.assertEqual(response.status_code, 404)
