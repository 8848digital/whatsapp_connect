# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe.utils import add_to_date, now_datetime

from whatsapp_connect.tests.utils import (
	IntegrationTestCase,
	make_account,
	make_template,
	random_number,
	sent,
)
from whatsapp_connect.whatsapp_connect_setup import setup_checks


class TestSetupChecks(IntegrationTestCase):
	"""The tests of the WhatsApp Setup page."""

	def setUp(self):
		"""One account."""
		self.account = make_account("Test Setup Account")

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_send_test_needs_hello_world(self):
		"""Without the hello_world template the user is told what to do."""
		frappe.db.delete("WhatsApp Template", {"template_name": "hello_world"})
		with self.assertRaises(frappe.ValidationError):
			setup_checks.send_test(self.account, random_number())

	def test_send_test_sends_hello_world(self):
		"""The approved hello_world template is sent."""
		make_template("hello_world", account=self.account, body="Hello World")
		with sent("wamid.SETUP"):
			result = setup_checks.send_test(self.account, random_number())
		self.assertEqual(result["status"], "Sent")

	def test_incoming_since_finds_a_new_message(self):
		"""A message received after the time is found; older ones are not."""
		since = add_to_date(now_datetime(), minutes=-1)
		self.assertFalse(setup_checks.incoming_since(self.account, since)["found"])
		frappe.get_doc(
			{
				"doctype": "WhatsApp Message",
				"direction": "Incoming",
				"whatsapp_account": self.account,
				"phone_number": random_number(),
				"message_type": "text",
				"body": "Hi",
				"status": "Received",
			}
		).insert(ignore_permissions=True)
		found = setup_checks.incoming_since(self.account, since)
		self.assertTrue(found["found"])
		self.assertEqual(found["body"], "Hi")

	def test_list_accounts_shows_the_hub_url(self):
		"""The page knows if Connect with Facebook is available."""
		frappe.db.set_single_value("WhatsApp Settings", "hub_url", "https://hub.example.com")
		status = setup_checks.list_accounts()
		self.assertEqual(status["hub_url"], "https://hub.example.com")
		self.assertIn(self.account, [a.name for a in status["accounts"]])
