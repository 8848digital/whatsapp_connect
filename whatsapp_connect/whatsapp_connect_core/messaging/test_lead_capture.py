# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import unittest
from unittest.mock import patch

import frappe

from whatsapp_connect.tests.webhook_case import WebhookTestCase
from whatsapp_connect.whatsapp_connect_core.messaging.contact_link import get_linked_contacts

SETTINGS = "whatsapp_connect.whatsapp_connect_core.messaging.lead_capture.get_settings"


class LeadCaptureCase(WebhookTestCase):
	"""Webhook tests with lead capture settings that are patched, not saved."""

	def use_settings(self, **values):
		"""Patch WhatsApp Settings for lead capture until the test ends."""
		settings = {"create_leads": 1, "lead_source": "WhatsApp Test", **values}
		patcher = patch(SETTINGS, return_value=frappe._dict(settings))
		patcher.start()
		self.addCleanup(patcher.stop)


@unittest.skipUnless(frappe.db.exists("DocType", "Lead"), "ERPNext is not installed")
class TestLeadCapture(LeadCaptureCase):
	"""A Lead for messages from numbers that match no record."""

	def setUp(self):
		"""Turn on lead capture with a source and an owner."""
		super().setUp()
		self.use_settings(lead_doctype="Lead", lead_owner="Administrator")

	def test_unknown_number_creates_one_lead(self):
		first = self.incoming(
			{"type": "text", "text": {"body": "Price of the blue kurta?"}}, name="Meera Iyer"
		)
		self.assertEqual(first.reference_doctype, "Lead")
		lead = frappe.get_doc("Lead", first.reference_name)
		self.assertEqual(
			(lead.lead_name, lead.mobile_no, lead.lead_owner),
			("Meera Iyer", f"+{self.number}", "Administrator"),
		)
		source_field = "source" if lead.meta.has_field("source") else "utm_source"
		self.assertEqual(lead.get(source_field), "WhatsApp Test")
		self.assertEqual(
			frappe.db.get_value("WhatsApp Profile", self.number, "assigned_to"), "Administrator"
		)

		# The next message finds the Lead (or the Contact ERPNext made for it): no second Lead.
		second = self.incoming({"type": "text", "text": {"body": "Hello?"}})
		linked = get_linked_contacts("Lead", lead.name)
		self.assertIn(
			(second.reference_doctype, second.reference_name),
			[("Lead", lead.name)] + [("Contact", name) for name in linked],
		)
		self.assertEqual(frappe.db.count("Lead", {"mobile_no": f"+{self.number}"}), 1)

	def test_known_number_creates_no_lead(self):
		contact = frappe.get_doc(
			{"doctype": "Contact", "first_name": "Karan", "phone_nos": [{"phone": f"+{self.number}"}]}
		).insert(ignore_permissions=True)
		message = self.incoming({"type": "text", "text": {"body": "Hi"}})
		self.assertEqual((message.reference_doctype, message.reference_name), ("Contact", contact.name))

	def test_setting_off_creates_no_lead(self):
		self.use_settings(create_leads=0)
		message = self.incoming({"type": "text", "text": {"body": "Hi"}})
		self.assertFalse(message.reference_doctype)

	def test_number_is_used_when_the_name_is_missing(self):
		message = self.incoming({"type": "text", "text": {"body": "Hi"}}, name=None)
		self.assertEqual(
			frappe.db.get_value("Lead", message.reference_name, "lead_name"), f"WhatsApp +{self.number}"
		)


@unittest.skipUnless(frappe.db.exists("DocType", "CRM Lead"), "Frappe CRM is not installed")
class TestCRMLeadCapture(LeadCaptureCase):
	"""A Frappe CRM Lead for messages from unknown numbers."""

	def setUp(self):
		"""Turn on lead capture for CRM Lead."""
		super().setUp()
		self.use_settings(lead_doctype="CRM Lead", lead_owner=None)

	def test_unknown_number_creates_one_crm_lead(self):
		first = self.incoming({"type": "text", "text": {"body": "Hi"}}, name="Neha Joshi")
		self.assertEqual(first.reference_doctype, "CRM Lead")
		lead = frappe.get_doc("CRM Lead", first.reference_name)
		self.assertEqual(
			(lead.first_name, lead.mobile_no, lead.source),
			("Neha Joshi", f"+{self.number}", "WhatsApp Test"),
		)
		second = self.incoming({"type": "text", "text": {"body": "Hello?"}})
		self.assertEqual((second.reference_doctype, second.reference_name), ("CRM Lead", lead.name))
