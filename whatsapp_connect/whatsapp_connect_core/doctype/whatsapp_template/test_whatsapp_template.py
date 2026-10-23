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
)
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template import template_meta
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_utils import (
	build_components,
)

UPLOAD_POST = "whatsapp_connect.whatsapp_connect_core.cloud_api.templates.requests.post"


class TestWhatsAppTemplate(IntegrationTestCase):
	"""Validation, Meta components, submit, sync, delete and status updates."""

	def setUp(self):
		"""Create the test account."""
		self.account = make_account()

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_name_is_normalized_and_checked(self):
		name = make_template("Order Update Two")
		self.assertEqual(name, "order_update_two-en")
		with self.assertRaises(frappe.ValidationError):
			make_template("bad-name!")

	def test_variables_need_samples_and_no_gaps(self):
		with self.assertRaises(frappe.ValidationError):
			make_template("test_missing_samples", body_samples="Asha")
		with self.assertRaises(frappe.ValidationError):
			make_template("test_gap", body="Hi {{1}} and {{3}}", body_samples="a\nb\nc")

	def test_components(self):
		template = frappe.get_doc(
			"WhatsApp Template",
			make_template(
				"test_components",
				header_type="Text",
				header_text="Order {{1}}",
				header_sample="SO-1",
				footer="Thanks",
				buttons=[
					{
						"button_type": "URL",
						"label": "Track",
						"url": "https://x.com/o/{{1}}",
						"url_sample": "https://x.com/o/SO-1",
					},
					{"button_type": "Phone Number", "label": "Call us", "phone_number": "+919900000000"},
					{"button_type": "Copy Code", "code_sample": "SAVE10"},
					{"button_type": "Quick Reply", "label": "Stop"},
				],
			),
		)
		header, body, footer, buttons = build_components(template)
		self.assertEqual(
			header,
			{
				"type": "HEADER",
				"format": "TEXT",
				"text": "Order {{1}}",
				"example": {"header_text": ["SO-1"]},
			},
		)
		self.assertEqual(body["example"], {"body_text": [["Asha", "SO-0001"]]})
		self.assertEqual(footer, {"type": "FOOTER", "text": "Thanks"})
		self.assertEqual(buttons["buttons"][0]["example"], ["https://x.com/o/SO-1"])
		self.assertEqual(buttons["buttons"][2], {"type": "COPY_CODE", "example": "SAVE10"})
		self.assertEqual(
			[b["type"] for b in buttons["buttons"]], ["URL", "PHONE_NUMBER", "COPY_CODE", "QUICK_REPLY"]
		)

	def test_authentication_components(self):
		template = frappe.get_doc(
			"WhatsApp Template",
			make_template(
				"test_otp",
				category="AUTHENTICATION",
				body="{{1}} is your code.",
				body_samples="",
				buttons=[{"button_type": "One-Time Password", "label": "Copy code"}],
			),
		)
		self.assertEqual(
			build_components(template),
			[
				{"type": "BODY", "add_security_recommendation": True},
				{
					"type": "BUTTONS",
					"buttons": [{"type": "OTP", "otp_type": "COPY_CODE", "text": "Copy code"}],
				},
			],
		)

	def test_submit_creates_then_updates(self):
		name = make_template("test_submit", status="Draft")
		with patch(
			REQUESTS, return_value=graph_response({"id": "tpl-1", "status": "PENDING"})
		) as request:
			self.assertEqual(template_meta.submit_template(name), "Pending")
		sent = request.call_args.kwargs["json"]
		self.assertEqual(
			(sent["name"], sent["language"], sent["category"]), ("test_submit", "en", "UTILITY")
		)
		self.assertEqual(frappe.db.get_value("WhatsApp Template", name, "meta_template_id"), "tpl-1")

		with patch(REQUESTS, return_value=graph_response({"success": True})) as request:
			template_meta.submit_template(name)
		self.assertTrue(request.call_args.args[1].endswith("/tpl-1"))

	def test_media_header_uploads_the_sample(self):
		file_doc = frappe.get_doc(
			{"doctype": "File", "file_name": "sample.txt", "content": b"x", "is_private": 1}
		).insert(ignore_permissions=True)
		frappe.db.set_value("WhatsApp Account", self.account, "app_id", "app-1")
		name = make_template(
			"test_media_header",
			status="Draft",
			header_type="Document",
			header_sample_file=file_doc.file_url,
		)
		answers = [
			graph_response({"id": "upload:1"}),
			graph_response({"id": "tpl-2", "status": "PENDING"}),
		]
		with patch(REQUESTS, side_effect=answers) as request, patch(
			UPLOAD_POST, return_value=graph_response({"h": "HANDLE"})
		):
			template_meta.submit_template(name)
		header = request.call_args.kwargs["json"]["components"][0]
		self.assertEqual(
			header, {"type": "HEADER", "format": "DOCUMENT", "example": {"header_handle": ["HANDLE"]}}
		)

	def test_sync_from_meta(self):
		meta = {
			"id": "tpl-9",
			"name": "test_synced",
			"language": "en_US",
			"status": "APPROVED",
			"category": "MARKETING",
			"components": [
				{"type": "HEADER", "format": "IMAGE"},
				{"type": "BODY", "text": "Hi {{1}}", "example": {"body_text": [["Asha"]]}},
				{
					"type": "BUTTONS",
					"buttons": [
						{"type": "URL", "text": "Shop", "url": "https://x.com/{{1}}", "example": ["https://x.com/a"]}
					],
				},
			],
		}
		pages = [
			graph_response({"data": [meta], "paging": {"cursors": {"after": "A"}, "next": "https://next"}}),
			graph_response({"data": []}),
		]
		with patch(REQUESTS, side_effect=pages):
			self.assertEqual(template_meta.sync_templates(self.account), 1)
		template = frappe.get_doc("WhatsApp Template", "test_synced-en_US")
		self.assertEqual(
			(template.status, template.category, template.header_type, template.body_samples),
			("Approved", "MARKETING", "Image", "Asha"),
		)
		self.assertEqual(
			(template.buttons[0].button_type, template.buttons[0].url_sample), ("URL", "https://x.com/a")
		)

	def test_delete_goes_on_when_meta_refuses(self):
		name = make_template("test_delete")
		frappe.db.set_value("WhatsApp Template", name, "meta_template_id", "tpl-5")
		with patch(
			REQUESTS,
			return_value=graph_response({"error": {"message": "Template not found", "code": 100}}, 400),
		):
			frappe.delete_doc("WhatsApp Template", name, ignore_permissions=True)
		self.assertFalse(frappe.db.exists("WhatsApp Template", name))

	def test_status_update_from_webhook(self):
		name = make_template("test_status", status="Pending")
		frappe.db.set_value("WhatsApp Template", name, "meta_template_id", "tpl-7")
		template_meta.update_template_status(
			{"event": "REJECTED", "message_template_id": 7 and "tpl-7", "reason": "INVALID_FORMAT"}
		)
		row = frappe.db.get_value("WhatsApp Template", name, ["status", "rejected_reason"], as_dict=True)
		self.assertEqual((row.status, row.rejected_reason), ("Rejected", "INVALID_FORMAT"))
