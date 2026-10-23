# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import json

import frappe

from whatsapp_connect.tests.utils import IntegrationTestCase, random_number
from whatsapp_connect.whatsapp_connect_campaign.doctype.whatsapp_recipient_list.recipient_list_utils import (
	import_recipients,
)


class TestWhatsAppRecipientList(IntegrationTestCase):
	"""Cleaning and importing recipients."""

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_numbers_are_cleaned(self):
		number = random_number()
		recipient_list = frappe.get_doc(
			{
				"doctype": "WhatsApp Recipient List",
				"list_name": f"Test {frappe.generate_hash(length=6)}",
				"recipients": [
					{"phone_number": f"+{number}"},
					{"phone_number": number},
					{"phone_number": "12"},
				],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(recipient_list.recipient_count, 1)
		self.assertEqual(recipient_list.recipients[0].phone_number, number)

	def test_import_from_doctype(self):
		number = random_number()
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Import",
				"last_name": frappe.generate_hash(length=6),
				"phone_nos": [{"phone": f"+{number}", "is_primary_mobile_no": 1}],
			}
		).insert(ignore_permissions=True)
		recipient_list = frappe.get_doc(
			{
				"doctype": "WhatsApp Recipient List",
				"list_name": f"Test {frappe.generate_hash(length=6)}",
				"source_doctype": "Contact",
				"phone_field": "mobile_no",
				"name_field": "first_name",
				"variable_fields": "first_name\nlast_name",
				"import_filters": json.dumps({"name": contact.name}),
			}
		).insert(ignore_permissions=True)
		self.assertEqual(import_recipients(recipient_list.name), 1)
		row = frappe.get_doc("WhatsApp Recipient List", recipient_list.name).recipients[0]
		self.assertEqual(
			(row.phone_number, row.recipient_name, row.variables),
			(number, "Import", f"Import|{contact.last_name}"),
		)
		self.assertEqual((row.reference_doctype, row.reference_name), ("Contact", contact.name))
