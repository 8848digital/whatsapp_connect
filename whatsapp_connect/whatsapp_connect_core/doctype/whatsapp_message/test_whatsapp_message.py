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
	random_number,
)
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_message.message_utils import (
	retry_message,
)
from whatsapp_connect.whatsapp_connect_core.messaging.opt_out import set_opted_out


class TestWhatsAppMessage(IntegrationTestCase):
	"""Sending messages: payloads, failures, retries and opt-out."""

	def setUp(self):
		"""Create the test account and a fresh number."""
		self.account = make_account()
		self.number = random_number()

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def send(self, answer=None, status=200, **values):
		"""
		Insert an outgoing message with the Graph API mocked.

		Returns:
		        tuple: (message document, mock of requests.request)
		"""
		answer = answer if answer is not None else {"messages": [{"id": "wamid.OK"}]}
		with patch(REQUESTS, return_value=graph_response(answer, status)) as request:
			message = frappe.get_doc(
				{
					"doctype": "WhatsApp Message",
					"whatsapp_account": self.account,
					"phone_number": f"+{self.number}",
					**values,
				}
			).insert(ignore_permissions=True)
		message.reload()
		return message, request

	def sent_body(self, request):
		"""Return the JSON body of the last Graph API call."""
		return request.call_args.kwargs["json"]

	def test_text_message_is_sent(self):
		message, request = self.send(body="Hello")
		self.assertEqual(message.status, "Sent")
		self.assertEqual(message.wamid, "wamid.OK")
		self.assertEqual(message.phone_number, self.number)
		body = self.sent_body(request)
		self.assertEqual(body["messaging_product"], "whatsapp")
		self.assertEqual(body["to"], self.number)
		self.assertEqual(body["text"], {"body": "Hello", "preview_url": True})
		self.assertTrue(request.call_args.args[1].endswith("/messages"))

	def test_reply_context(self):
		_message, request = self.send(body="Yes", reply_to_wamid="wamid.EARLIER")
		self.assertEqual(self.sent_body(request)["context"], {"message_id": "wamid.EARLIER"})

	def test_meta_error_keeps_a_failed_message(self):
		error = {
			"error": {
				"message": "Recipient not on WhatsApp",
				"code": 131026,
				"error_data": {"details": "Check the number"},
			}
		}
		message, _request = self.send(answer=error, status=400, body="Hello")
		self.assertEqual(message.status, "Failed")
		self.assertEqual(message.error_code, "131026")
		self.assertEqual(message.error_message, "Recipient not on WhatsApp - Check the number")

	def test_retry_failed_message(self):
		message, _request = self.send(
			answer={"error": {"message": "Busy", "code": 130429}}, status=400, body="Hello"
		)
		with patch(REQUESTS, return_value=graph_response({"messages": [{"id": "wamid.RETRY"}]})):
			status = retry_message(message.name)
		self.assertEqual(status, "Sent")
		self.assertEqual(frappe.db.get_value("WhatsApp Message", message.name, "wamid"), "wamid.RETRY")

	def test_reply_buttons(self):
		options = [{"id": "yes", "title": "Yes"}, {"id": "no", "title": "No"}]
		_message, request = self.send(
			message_type="interactive", body="Confirm?", interactive_options=json.dumps(options)
		)
		interactive = self.sent_body(request)["interactive"]
		self.assertEqual(interactive["type"], "button")
		self.assertEqual(
			interactive["action"]["buttons"][1], {"type": "reply", "reply": {"id": "no", "title": "No"}}
		)

	def test_list_for_more_than_three_options(self):
		options = [{"id": f"o{index}", "title": f"Option {index}"} for index in range(5)]
		_message, request = self.send(
			message_type="interactive",
			body="Pick one",
			interactive_options=json.dumps(options),
			list_button_label="Choose",
		)
		interactive = self.sent_body(request)["interactive"]
		self.assertEqual(interactive["type"], "list")
		self.assertEqual(interactive["action"]["button"], "Choose")
		self.assertEqual(len(interactive["action"]["sections"][0]["rows"]), 5)

	def test_reaction(self):
		_message, request = self.send(
			message_type="reaction", reply_to_wamid="wamid.X", reaction_emoji="👍"
		)
		body = self.sent_body(request)
		self.assertEqual(body["reaction"], {"message_id": "wamid.X", "emoji": "👍"})
		self.assertNotIn("context", body)

	def test_local_document_is_uploaded(self):
		file_doc = frappe.get_doc(
			{"doctype": "File", "file_name": "invoice.txt", "content": b"invoice", "is_private": 1}
		).insert(ignore_permissions=True)
		answer = {"id": "media-77", "messages": [{"id": "wamid.DOC"}]}
		message, request = self.send(
			answer=answer, message_type="document", attachment=file_doc.file_url, body="Your invoice"
		)
		upload, send = request.call_args_list
		self.assertTrue(upload.args[1].endswith("/media"))
		self.assertEqual(upload.kwargs["files"]["file"][0], "invoice.txt")
		self.assertEqual(
			send.kwargs["json"]["document"],
			{"id": "media-77", "filename": "invoice.txt", "caption": "Your invoice"},
		)
		self.assertEqual(message.media_id, "media-77")

	def test_external_image_is_sent_as_link(self):
		_message, request = self.send(message_type="image", attachment="https://example.com/a.png")
		self.assertEqual(self.sent_body(request)["image"], {"link": "https://example.com/a.png"})

	def test_template_to_opted_out_number_is_not_sent(self):
		set_opted_out(self.number, True, self.account)
		message, request = self.send(message_type="template")
		self.assertEqual(message.status, "Opted Out")
		request.assert_not_called()

	def test_skip_send_flag(self):
		frappe.db.set_value("WhatsApp Account", {"name": ["!=", self.account]}, "default_outgoing", 0)
		frappe.db.set_value("WhatsApp Account", self.account, "default_outgoing", 1)
		with patch(REQUESTS) as request:
			message = frappe.get_doc(
				{"doctype": "WhatsApp Message", "phone_number": self.number, "body": "x"}
			)
			message.flags.skip_send = True
			message.insert(ignore_permissions=True)
		request.assert_not_called()
		self.assertEqual(message.whatsapp_account, self.account)

	def test_invalid_number_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "WhatsApp Message", "phone_number": "12", "body": "x"}).insert(
				ignore_permissions=True
			)

	def test_incoming_message_is_linked_to_contact(self):
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Link",
				"last_name": "Test",
				"phone_nos": [
					{
						"phone": f"+{self.number[:2]} {self.number[2:7]}-{self.number[7:]}",
						"is_primary_mobile_no": 1,
					}
				],
			}
		).insert(ignore_permissions=True)
		message = frappe.get_doc(
			{
				"doctype": "WhatsApp Message",
				"direction": "Incoming",
				"phone_number": self.number,
				"body": "hi",
				"whatsapp_account": self.account,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(
			(message.status, message.reference_doctype, message.reference_name),
			("Received", "Contact", contact.name),
		)
		self.assertEqual(frappe.db.get_value("WhatsApp Profile", self.number, "contact"), contact.name)
