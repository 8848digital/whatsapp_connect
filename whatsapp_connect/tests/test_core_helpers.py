# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import unittest
from unittest.mock import patch

import frappe
from frappe.utils import add_days, now_datetime

from whatsapp_connect.tests.utils import (
	REQUESTS,
	IntegrationTestCase,
	graph_response,
	make_account,
	random_number,
)
from whatsapp_connect.whatsapp_connect_core import tasks
from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI, CloudAPIError
from whatsapp_connect.whatsapp_connect_core.messaging import contact_link
from whatsapp_connect.whatsapp_connect_core.messaging.contact_link import find_reference
from whatsapp_connect.whatsapp_connect_core.messaging.timeline import get_timeline_content
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number, number_suffix


class TestPhone(unittest.TestCase):
	"""Number normalization without the database."""

	def test_international_formats(self):
		self.assertEqual(normalize_number("+91 99000-00101", ""), "919900000101")
		self.assertEqual(normalize_number("0091 99000 00101", ""), "919900000101")

	def test_national_numbers_get_the_country_code(self):
		self.assertEqual(normalize_number("099000 00101", "91"), "919900000101")
		self.assertEqual(normalize_number("9900000101", "+91"), "919900000101")

	def test_unusable_numbers(self):
		self.assertIsNone(normalize_number("", "91"))
		self.assertIsNone(normalize_number("123", ""))
		self.assertEqual(number_suffix("+91 99000 00101"), "9900000101")


class TestCloudAPI(IntegrationTestCase):
	"""The Graph API client: success, errors, rate limits and logging."""

	def setUp(self):
		"""Create the test account."""
		self.api = CloudAPI(make_account())

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_send_returns_wamid_and_logs_the_call(self):
		logs = frappe.db.count("WhatsApp Log", {"log_type": "API Request"})
		with patch(REQUESTS, return_value=graph_response({"messages": [{"id": "wamid.A"}]})) as request:
			self.assertEqual(
				self.api.send_message({"to": "919900000101", "type": "text", "text": {"body": "x"}}), "wamid.A"
			)
		self.assertEqual(request.call_args.kwargs["headers"], {"Authorization": "Bearer test-token"})
		self.assertEqual(frappe.db.count("WhatsApp Log", {"log_type": "API Request"}), logs + 1)
		log = frappe.get_last_doc("WhatsApp Log")
		self.assertNotIn("test-token", (log.request or "") + (log.response or ""))

	def test_error_is_mapped(self):
		error = {
			"error": {
				"message": "Too many messages",
				"code": 130429,
				"error_data": {"details": "Slow down"},
			}
		}
		with patch(REQUESTS, return_value=graph_response(error, 400)), self.assertRaises(
			CloudAPIError
		) as caught:
			self.api.send_message({})
		self.assertTrue(caught.exception.is_rate_limit)
		self.assertEqual(caught.exception.describe(), "Too many messages - Slow down")


class TestContactLinkAndTimeline(IntegrationTestCase):
	"""Finding records by number and showing messages in timelines."""

	def setUp(self):
		"""Create the test account and a contact with a formatted number."""
		self.account = make_account()
		self.number = random_number()
		self.contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Timeline",
				"last_name": "Test",
				"phone_nos": [
					{
						"phone": f"+{self.number[:2]} ({self.number[2:7]}) {self.number[7:]}",
						"is_primary_mobile_no": 1,
					}
				],
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_find_reference(self):
		for number in (self.number, "+" + self.number, "0" + self.number[2:]):
			self.assertEqual(find_reference(number), ("Contact", self.contact.name))
		self.assertEqual(find_reference(random_number()), (None, None))

	def test_timeline_cards_and_party_contacts(self):
		message = frappe.get_doc(
			{
				"doctype": "WhatsApp Message",
				"direction": "Incoming",
				"phone_number": self.number,
				"body": "<b>hi</b>",
				"whatsapp_account": self.account,
			}
		).insert(ignore_permissions=True)
		cards = get_timeline_content("Contact", self.contact.name)
		self.assertIn(message.name, cards[0]["content"])
		self.assertIn("whatsapp-connect-reply", cards[0]["content"])
		self.assertNotIn("<b>", cards[0]["content"])

		self.contact.append("links", {"link_doctype": "Role", "link_name": "System Manager"})
		self.contact.save(ignore_permissions=True)
		with patch.object(contact_link, "PARTY_DOCTYPES", ("Role",)):
			self.assertTrue(get_timeline_content("Role", "System Manager"))

	def test_no_cards_without_read_permission(self):
		with patch(
			"whatsapp_connect.whatsapp_connect_core.messaging.timeline.frappe.has_permission",
			return_value=False,
		):
			self.assertEqual(get_timeline_content("Contact", self.contact.name), [])


class TestTasks(IntegrationTestCase):
	"""Scheduled jobs."""

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_old_logs_are_cleared(self):
		old = frappe.get_doc({"doctype": "WhatsApp Log", "log_type": "Webhook"}).insert(
			ignore_permissions=True
		)
		frappe.db.set_value("WhatsApp Log", old.name, "creation", add_days(now_datetime(), -40))
		new = frappe.get_doc({"doctype": "WhatsApp Log", "log_type": "Webhook"}).insert(
			ignore_permissions=True
		)
		frappe.db.set_single_value("WhatsApp Settings", "log_retention_days", 30)
		tasks.clear_old_logs()
		self.assertFalse(frappe.db.exists("WhatsApp Log", old.name))
		self.assertTrue(frappe.db.exists("WhatsApp Log", new.name))


class TestTimelineTemplateCard(IntegrationTestCase):
	"""A sent template shows its name on the timeline card."""

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_template_name_on_card(self):
		from whatsapp_connect.tests.utils import make_template

		account = make_account()
		template = make_template("test_timeline_card")
		contact = frappe.get_doc({"doctype": "Contact", "first_name": "Card"}).insert(
			ignore_permissions=True
		)
		message = frappe.get_doc(
			{
				"doctype": "WhatsApp Message",
				"phone_number": random_number(),
				"message_type": "template",
				"template": template,
				"whatsapp_account": account,
				"reference_doctype": "Contact",
				"reference_name": contact.name,
				"status": "Sent",
			}
		)
		message.flags.skip_send = True
		message.insert(ignore_permissions=True)
		self.assertIn(
			f"Template: {template}", get_timeline_content("Contact", contact.name)[0]["content"]
		)
