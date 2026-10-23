# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import json
from unittest.mock import patch

import frappe

from whatsapp_connect.tests.utils import (
	REQUESTS,
	IntegrationTestCase,
	graph_response,
	make_account,
	make_template,
	random_number,
)
from whatsapp_connect.whatsapp_connect_core.messaging.template_params import clean_param
from whatsapp_connect.whatsapp_connect_core.messaging.template_preview import render_preview
from whatsapp_connect.whatsapp_connect_core.messaging.template_send import send_template


class TestTemplateSend(IntegrationTestCase):
	"""Sending templates with values from documents."""

	def setUp(self):
		"""Create the test account, a contact and a fresh number."""
		self.account = make_account()
		self.number = random_number()
		self.contact = frappe.get_doc(
			{"doctype": "Contact", "first_name": "Asha", "last_name": "Traders"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def send(self, template, **kwargs):
		"""Send with the Graph API mocked; return (message, sent body)."""
		with patch(
			REQUESTS, return_value=graph_response({"messages": [{"id": "wamid.T"}], "id": "media-1"})
		) as request:
			message = send_template(template, self.number, **kwargs)
		return message, (request.call_args.kwargs.get("json") if request.called else None)

	def test_values_from_document_fields(self):
		template = make_template(
			"test_doc_values",
			body_fields="first_name\nlast_name",
			header_type="Text",
			header_text="Hi {{1}}",
			header_sample="x",
			header_field="first_name",
			buttons=[
				{
					"button_type": "URL",
					"label": "Open",
					"url": "https://x.com/{{1}}",
					"url_sample": "https://x.com/a",
					"value_field": "name",
				}
			],
		)
		message, body = self.send(template, doc=self.contact, source="Test")
		self.assertEqual(message.status, "Sent")
		components = body["template"]["components"]
		self.assertEqual(body["template"]["name"], "test_doc_values")
		self.assertEqual(
			components[0], {"type": "header", "parameters": [{"type": "text", "text": "Asha"}]}
		)
		self.assertEqual(
			components[1]["parameters"],
			[{"type": "text", "text": "Asha"}, {"type": "text", "text": "Traders"}],
		)
		self.assertEqual(
			components[2],
			{
				"type": "button",
				"sub_type": "url",
				"index": "0",
				"parameters": [{"type": "text", "text": self.contact.name}],
			},
		)
		self.assertEqual(
			(message.reference_doctype, message.reference_name, message.source),
			("Contact", self.contact.name, "Test"),
		)

	def test_given_values_win(self):
		template = make_template("test_given_values", body_fields="first_name\nlast_name")
		_message, body = self.send(template, doc=self.contact, values={"body": ["Ravi", "SO-9"]})
		self.assertEqual(
			[p["text"] for p in body["template"]["components"][0]["parameters"]], ["Ravi", "SO-9"]
		)

	def test_copy_code_and_flow_buttons(self):
		template = make_template(
			"test_code_flow",
			buttons=[
				{"button_type": "Copy Code", "code_sample": "SAVE10"},
				{"button_type": "Flow", "label": "Book", "flow_id": "flow-1"},
			],
		)
		_message, body = self.send(template, values={"buttons": {"0": "WELCOME5"}})
		buttons = body["template"]["components"][1:]
		self.assertEqual(buttons[0]["parameters"], [{"type": "coupon_code", "coupon_code": "WELCOME5"}])
		self.assertEqual(
			(buttons[1]["sub_type"], len(buttons[1]["parameters"][0]["action"]["flow_token"])), ("flow", 16)
		)

	def test_document_header_link(self):
		template = make_template("test_doc_header", header_type="Document")
		_message, body = self.send(
			template,
			values={"header_media": "https://example.com/invoice.pdf", "header_filename": "Invoice.pdf"},
		)
		header = body["template"]["components"][0]
		self.assertEqual(
			header["parameters"][0],
			{
				"type": "document",
				"document": {"link": "https://example.com/invoice.pdf", "filename": "Invoice.pdf"},
			},
		)

	def test_unapproved_template_fails_with_reason(self):
		template = make_template("test_pending", status="Pending")
		message, body = self.send(template)
		self.assertIsNone(body)
		self.assertEqual(message.status, "Failed")
		self.assertIn("not approved", message.error_message)

	def test_clean_param(self):
		self.assertEqual(clean_param("<p>Line 1</p>\n\tLine     2"), "Line 1 Line 2")
		self.assertEqual(len(clean_param("x" * 2000)), 1024)

	def test_preview(self):
		template = make_template(
			"test_preview",
			body_fields="first_name",
			body="Hello *{{1}}*",
			body_samples="Sample",
			footer="Bye",
		)
		preview = render_preview(template, "Contact", self.contact.name)
		self.assertEqual((preview["body"], preview["footer"]), ("Hello *Asha*", "Bye"))
		self.assertEqual(render_preview(template)["body"], "Hello *Sample*")
