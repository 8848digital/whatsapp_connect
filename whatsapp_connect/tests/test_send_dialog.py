# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe
from frappe.utils import now_datetime

from whatsapp_connect.tests.utils import (
	REQUESTS,
	IntegrationTestCase,
	graph_response,
	make_account,
	make_template,
	random_number,
)
from whatsapp_connect.whatsapp_connect_core.api.v1 import send
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_profile.profile_utils import (
	record_incoming,
)

OK = {"messages": [{"id": "wamid.D"}]}


class TestSendDialog(IntegrationTestCase):
	"""The Send WhatsApp dialog endpoints."""

	def setUp(self):
		"""Create the default account, a template, and a contact with a number."""
		self.account = make_account()
		frappe.db.set_value("WhatsApp Account", {"name": ["!=", self.account]}, "default_outgoing", 0)
		frappe.db.set_value("WhatsApp Account", self.account, "default_outgoing", 1)
		self.template = make_template("test_dialog", body_fields="first_name\nlast_name")
		self.number = random_number()
		self.contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Asha",
				"last_name": "Traders",
				"phone_nos": [{"phone": f"+{self.number}", "is_primary_mobile_no": 1}],
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_options_list_the_numbers_with_window_state(self):
		data = send.options("Contact", self.contact.name)["data"]
		self.assertEqual([(row["number"], row["window_open"]) for row in data], [(self.number, False)])
		record_incoming(self.number, None, self.account, now_datetime())
		self.assertTrue(send.options("Contact", self.contact.name)["data"][0]["window_open"])

	def test_send_template_from_the_document(self):
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			result = send.send_template_message(self.template, self.number, "Contact", self.contact.name)
		self.assertTrue(result["status"])
		parameters = request.call_args.kwargs["json"]["template"]["components"][0]["parameters"]
		self.assertEqual([p["text"] for p in parameters], ["Asha", "Traders"])
		message = frappe.get_doc("WhatsApp Message", result["data"]["message"])
		self.assertEqual(
			(message.reference_doctype, message.reference_name), ("Contact", self.contact.name)
		)

	def test_failed_send_returns_the_reason(self):
		with patch(
			REQUESTS,
			return_value=graph_response({"error": {"message": "Not on WhatsApp", "code": 131026}}, 400),
		):
			result = send.send_template_message(self.template, self.number, "Contact", self.contact.name)
		self.assertEqual(
			(result["status"], result["status_code"], result["message"]), (False, 422, "Not on WhatsApp")
		)

	def test_reply_only_inside_the_window(self):
		with patch(REQUESTS) as request, self.assertRaises(frappe.ValidationError):
			send.send_reply_message(self.number, "Hello")
		request.assert_not_called()

		record_incoming(self.number, None, self.account, now_datetime())
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			result = send.send_reply_message(self.number, "Hello", "Contact", self.contact.name)
		self.assertEqual(request.call_args.kwargs["json"]["text"]["body"], "Hello")
		self.assertTrue(result["status"])
