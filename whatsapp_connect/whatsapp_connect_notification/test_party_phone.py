# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe

from whatsapp_connect.tests.utils import IntegrationTestCase, random_number
from whatsapp_connect.whatsapp_connect_notification.party_phone import get_party_number


class TestPartyPhone(IntegrationTestCase):
	"""The party's mobile number, for Payment Entry, Payment Request and similar documents."""

	def setUp(self):
		"""Create a contact with a number in its phone table."""
		self.number = random_number()
		self.contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Party",
				"last_name": "Phone",
				"phone_nos": [{"phone": f"+{self.number}", "is_primary_mobile_no": 1}],
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_contact_mobile_first(self):
		other = random_number()
		self.assertEqual(
			get_party_number(frappe._dict(contact_mobile=f"+{other}", contact_person=self.contact.name)),
			other,
		)

	def test_contact_person(self):
		self.assertEqual(get_party_number(frappe._dict(contact_person=self.contact.name)), self.number)

	def test_customer_and_its_contacts(self):
		if "erpnext" not in frappe.get_installed_apps():
			self.skipTest("ERPNext is not installed")
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": f"Party {frappe.generate_hash(length=6)}",
				"customer_type": "Company",
				"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}),
				"territory": frappe.db.get_value("Territory", {"is_group": 0}),
			}
		).insert(ignore_permissions=True, ignore_mandatory=True)
		self.contact.append("links", {"link_doctype": "Customer", "link_name": customer.name})
		self.contact.save(ignore_permissions=True)
		payment = frappe._dict(doctype="Payment Entry", party_type="Customer", party=customer.name)
		self.assertEqual(get_party_number(payment), self.number)
		self.assertIsNone(get_party_number(frappe._dict(party_type="Customer", party="Nobody")))
