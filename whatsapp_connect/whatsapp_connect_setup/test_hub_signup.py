# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.utils.password import get_decrypted_password

from whatsapp_connect.tests.setup_fakes import FakeGraph, enable_hub
from whatsapp_connect.tests.utils import REQUESTS, IntegrationTestCase
from whatsapp_connect.whatsapp_connect_setup import hub_client
from whatsapp_connect.whatsapp_connect_setup.hub import signup

EXCHANGE = "whatsapp_connect.whatsapp_connect_setup.hub.meta.requests.get"
HUB_POST = "whatsapp_connect.whatsapp_connect_setup.hub_client.requests.post"
SITE = "http://erp.example.com"


def hub_post(url, json=None, timeout=None):
	"""Send a hub_client call straight to this site's hub functions (this site is both)."""
	method = url.rsplit(".", 1)[-1]
	response = MagicMock(ok=True)
	try:
		data = getattr(signup, method)(**json)
		response.json.return_value = {"message": {"status": True, "data": data}}
	except frappe.ValidationError as exc:
		response.ok = False
		response.json.return_value = {
			"_server_messages": frappe.as_json([frappe.as_json({"message": str(exc)})])
		}
	return response


class TestHubSignup(IntegrationTestCase):
	"""Connect with Facebook: session, code exchange, claim and disconnect."""

	def setUp(self):
		"""This site is the hub and its own client."""
		enable_hub()
		frappe.db.set_single_value("WhatsApp Settings", "hub_url", "https://hub.example.com")
		suffix = frappe.generate_hash(length=8)
		self.waba, self.phone = f"waba-{suffix}", f"phone-{suffix}"
		self.graph = FakeGraph("hub-app", self.waba, self.phone)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def start(self, coexistence=0):
		"""Open a session through hub_client, as the setup page does."""
		with patch(HUB_POST, side_effect=hub_post):
			return hub_client.start_signup(coexistence)["session"]

	def finish(self, session, event="FINISH"):
		"""Finish the signup as the hub page does after Meta's popup."""
		exchange = MagicMock()
		exchange.json.return_value = {"access_token": "business-token"}
		with patch(EXCHANGE, return_value=exchange), patch(REQUESTS, side_effect=self.graph):
			return signup.finish(session, "code-1", self.waba, self.phone, event)

	def complete(self, session):
		"""Claim the signup and run the setup steps on this site."""
		with patch(HUB_POST, side_effect=hub_post), patch(REQUESTS, side_effect=self.graph):
			return hub_client.complete_signup(session)

	def test_full_signup_creates_an_embedded_signup_account(self):
		"""The site gets the token, keeps the forwarding secret as App Secret and registers the number."""
		session = self.start()
		self.finish(session)
		self.assertIn(f"{self.waba}/subscribed_apps", self.graph.paths())
		result = self.complete(session)
		account = frappe.get_doc("WhatsApp Account", result["account"])
		self.assertEqual(account.setup_method, "Embedded Signup")
		self.assertEqual(account.get_password("access_token"), "business-token")
		self.assertEqual(account.app_id, "hub-app")
		connection = frappe.get_doc("WhatsApp Hub Connection", session)
		self.assertEqual(account.get_password("app_secret"), connection.get_password("forward_secret"))
		self.assertIn(f"connection={session}", account.flow_endpoint_url)
		self.assertIn(f"{self.phone}/register", self.graph.paths())
		self.assertNotIn("subscriptions", " ".join(self.graph.paths()))
		failed = [step for step in result["steps"] if not step["ok"]]
		self.assertEqual(failed, [], failed)

	def test_claim_deletes_the_token_on_the_hub(self):
		"""After the claim the hub keeps no customer token, and a second claim fails."""
		session = self.start()
		self.finish(session)
		self.complete(session)
		self.assertEqual(frappe.db.get_value("WhatsApp Hub Connection", session, "status"), "Claimed")
		token = get_decrypted_password(
			"WhatsApp Hub Connection", session, "access_token", raise_exception=False
		)
		self.assertFalse(token)
		with self.assertRaises(frappe.ValidationError):
			self.complete(session)

	def test_claim_needs_the_claim_secret(self):
		"""Only the site that started the session can claim it."""
		session = self.start()
		self.finish(session)
		with self.assertRaises(frappe.PermissionError):
			signup.claim(session, "wrong-secret")

	def test_coexistence_numbers_are_not_registered(self):
		"""A number that stays on the WhatsApp Business app must not be registered again."""
		session = self.start(coexistence=1)
		self.finish(session, event="FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING")
		self.complete(session)
		self.assertNotIn(f"{self.phone}/register", self.graph.paths())

	def test_finish_refuses_a_number_of_another_account(self):
		"""The chosen number must belong to the chosen business account."""
		session = self.start()
		self.phone = "phone-of-someone-else"
		with self.assertRaises(frappe.ValidationError):
			self.finish(session)

	def test_finish_refuses_a_cancelled_signup(self):
		"""Without a finish event there is nothing to connect."""
		session = self.start()
		with self.assertRaises(frappe.ValidationError):
			self.finish(session, event="CANCEL")

	def test_hub_refuses_private_sites_unless_allowed(self):
		"""Without Allow HTTP and Private Sites, the hub only calls public https sites."""
		enable_hub(allow_insecure_sites=0)
		with self.assertRaises(frappe.ValidationError):
			signup.start(SITE, f"{SITE}/a", f"{SITE}/b")
		with self.assertRaises(frappe.ValidationError):
			signup.start("https://localhost", "https://localhost/a", "https://localhost/b")

	def test_hub_refuses_urls_of_another_site(self):
		"""The webhook URL must be on the site that opens the session."""
		with self.assertRaises(frappe.ValidationError):
			signup.start(SITE, "http://evil.example.com/a", f"{SITE}/b")

	def test_disabled_hub_refuses_everything(self):
		"""A normal site is not a hub."""
		enable_hub(enabled=0)
		with self.assertRaises(frappe.PermissionError):
			signup.start(SITE, f"{SITE}/a", f"{SITE}/b")

	def test_disconnect_needs_the_forwarding_secret(self):
		"""The site proves it holds the forwarding secret; the account is disabled."""
		session = self.start()
		self.finish(session)
		account = self.complete(session)["account"]
		with self.assertRaises(frappe.PermissionError):
			signup.disconnect(session, "bad-signature")
		with patch(HUB_POST, side_effect=hub_post):
			hub_client.disconnect(account)
		self.assertEqual(
			frappe.db.get_value("WhatsApp Hub Connection", session, "status"), "Disconnected"
		)
		self.assertFalse(frappe.db.get_value("WhatsApp Account", account, "enabled"))

	def test_hub_errors_reach_the_user(self):
		"""The hub's error text is shown on the site."""
		with patch(HUB_POST, side_effect=hub_post), self.assertRaises(frappe.ValidationError) as error:
			hub_client.call_hub("claim", {"session": "nope", "claim_secret": "x"})
		self.assertIn("not valid", str(error.exception))
