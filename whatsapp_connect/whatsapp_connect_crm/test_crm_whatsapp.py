# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import unittest
from unittest.mock import patch

import frappe
from frappe.utils import now_datetime

from whatsapp_connect.tests.utils import REQUESTS, graph_response, make_template
from whatsapp_connect.tests.webhook_case import WebhookTestCase
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_profile.profile_utils import (
	record_incoming,
)
from whatsapp_connect.whatsapp_connect_crm.api.v1 import crm_whatsapp

OK = {"messages": [{"id": "wamid.CRM"}]}


@unittest.skipUnless("crm" in frappe.get_installed_apps(), "Frappe CRM is not installed")
class TestCRMWhatsApp(WebhookTestCase):
	"""The Frappe CRM WhatsApp tab, served by WhatsApp Connect."""

	def setUp(self):
		"""Create a CRM Lead with the test number."""
		super().setUp()
		self.lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Meera", "mobile_no": f"+{self.number}"}
		).insert(ignore_permissions=True)

	def test_crm_hooks_do_not_break_messages(self):
		message = self.incoming({"type": "text", "text": {"body": "Hi"}})
		self.assertEqual((message.type, message.message), ("Incoming", "Hi"))

	def test_messages_of_the_lead_numbers(self):
		question = self.incoming({"type": "text", "text": {"body": "Is it in stock?"}}, name="Meera")
		self.incoming(
			{"type": "reaction", "reaction": {"message_id": question.wamid, "emoji": "👍"}}, name="Meera"
		)
		self.incoming(
			{"type": "text", "text": {"body": "Size M"}, "context": {"id": question.wamid}}, name="Meera"
		)

		rows = crm_whatsapp.get_whatsapp_messages("CRM Lead", self.lead.name)
		self.assertEqual([row["message"] for row in rows], ["Is it in stock?", "Size M"])
		first, reply = rows
		self.assertEqual(
			(first["type"], first["from"], first["from_name"]), ("Incoming", self.number, "Meera")
		)
		self.assertEqual(first["reaction"], "👍")
		self.assertEqual((reply["is_reply"], reply["reply_message"]), (True, "Is it in stock?"))

	def test_send_text_and_template_from_the_lead(self):
		record_incoming(self.number, None, self.account, now_datetime())
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			name = crm_whatsapp.create_whatsapp_message("CRM Lead", self.lead.name, "Booked", self.number)
		self.assertEqual(request.call_args.kwargs["json"]["text"]["body"], "Booked")
		message = frappe.get_doc("WhatsApp Message", name)
		self.assertEqual(
			(message.reference_doctype, message.reference_name), ("CRM Lead", self.lead.name)
		)

		template = make_template("test_crm_template", account=self.account)
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			crm_whatsapp.send_whatsapp_template("CRM Lead", self.lead.name, template, self.number)
		self.assertEqual(request.call_args.kwargs["json"]["type"], "template")

	def test_free_text_needs_an_open_window(self):
		with patch(REQUESTS) as request, self.assertRaises(frappe.ValidationError):
			crm_whatsapp.create_whatsapp_message("CRM Lead", self.lead.name, "Hello", self.number)
		request.assert_not_called()

	def test_users_without_a_sales_role_are_refused(self):
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				crm_whatsapp.get_whatsapp_messages("CRM Lead", self.lead.name)
		finally:
			frappe.set_user("Administrator")

	def test_template_list_for_the_picker(self):
		template = make_template("test_crm_picker", account=self.account)
		rows = frappe.get_list("WhatsApp Templates", fields=["name", "template", "footer"])
		row = next(row for row in rows if row["name"] == template)
		self.assertEqual(
			(row["status"], row["template"]), ("APPROVED", "Hello {{1}}, your order {{2}} is ready.")
		)
