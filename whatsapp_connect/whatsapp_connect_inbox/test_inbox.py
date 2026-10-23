# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import json
from unittest.mock import patch

import frappe
from frappe.utils import now_datetime

from whatsapp_connect.tests.utils import REQUESTS, graph_response, make_template
from whatsapp_connect.tests.webhook_case import WebhookTestCase
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_profile.profile_utils import (
	record_incoming,
)
from whatsapp_connect.whatsapp_connect_inbox.api.v1 import inbox, send

OK = {"messages": [{"id": "wamid.INBOX"}], "id": "media-1"}


class TestInbox(WebhookTestCase):
	"""Conversations, assignment and sending from the WhatsApp Inbox."""

	def profile(self):
		"""Return the test number's WhatsApp Profile."""
		return frappe.get_doc("WhatsApp Profile", self.number)

	def open_window(self):
		"""Note a message from the customer now, so free text is allowed."""
		record_incoming(self.number, None, self.account, now_datetime())

	def test_incoming_message_opens_an_unread_conversation(self):
		self.incoming({"type": "text", "text": {"body": "Is the kurta in stock?"}})
		self.incoming({"type": "image", "image": {"id": "media-2", "mime_type": "image/jpeg"}})
		profile = self.profile()
		self.assertEqual(
			(profile.conversation_status, profile.unread_count, profile.last_message_direction),
			("Open", 2, "Incoming"),
		)
		self.assertEqual(profile.last_message_preview, "Photo")

	def test_reaction_does_not_change_the_preview(self):
		self.incoming({"type": "text", "text": {"body": "Thanks"}})
		self.incoming({"type": "reaction", "reaction": {"message_id": "wamid.X", "emoji": "👍"}})
		self.assertEqual(
			(self.profile().last_message_preview, self.profile().unread_count), ("Thanks", 1)
		)

	def test_closed_conversation_opens_again(self):
		self.incoming({"type": "text", "text": {"body": "Hi"}})
		inbox.set_status(self.number, "Closed")
		self.incoming({"type": "text", "text": {"body": "One more question"}})
		self.assertEqual(self.profile().conversation_status, "Open")

	def test_list_filters_and_counts(self):
		name = f"Meera {frappe.generate_hash(length=6)}"
		self.incoming({"type": "text", "text": {"body": "Hi"}}, name=name)
		data = inbox.get_conversations(status="Open", search=name)["data"]
		self.assertEqual([row["phone_number"] for row in data["conversations"]], [self.number])
		self.assertGreaterEqual(data["counts"]["Open"], 1)

		inbox.assign(self.number, "Administrator")
		mine = inbox.get_conversations(assigned_to="me", search=self.number)["data"]["conversations"]
		self.assertEqual(mine[0]["assigned_to"], "Administrator")
		unassigned = inbox.get_conversations(assigned_to="unassigned", search=self.number)["data"]
		self.assertEqual(unassigned["conversations"], [])

	def test_numbers_that_never_wrote_are_not_conversations(self):
		self.outgoing("wamid.CAMPAIGN")
		data = inbox.get_conversations(search=self.number)["data"]
		self.assertEqual(data["conversations"], [])

	def test_open_conversation_and_mark_read(self):
		self.incoming({"type": "text", "text": {"body": "Hello"}})
		data = inbox.get_conversation(self.number)["data"]
		self.assertEqual([row["body"] for row in data["messages"]], ["Hello"])
		inbox.mark_read(self.number)
		self.assertEqual(self.profile().unread_count, 0)

	def test_assign_only_to_agents(self):
		self.incoming({"type": "text", "text": {"body": "Hi"}})
		with self.assertRaises(frappe.ValidationError):
			inbox.assign(self.number, "Guest")
		inbox.assign(self.number, "")
		self.assertIsNone(self.profile().assigned_to)

	def test_send_text_as_a_reply(self):
		question = self.incoming({"type": "text", "text": {"body": "Price?"}})
		self.open_window()
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			result = send.send_text(self.number, "It is 1,200", reply_to=question.name)
		self.assertTrue(result["status"])
		payload = request.call_args.kwargs["json"]
		self.assertEqual(
			(payload["text"]["body"], payload["context"]["message_id"]), ("It is 1,200", question.wamid)
		)
		self.assertEqual(self.profile().last_message_direction, "Outgoing")

	def test_free_text_needs_an_open_window(self):
		self.incoming({"type": "text", "text": {"body": "Old message"}})
		with patch(REQUESTS) as request, self.assertRaises(frappe.ValidationError):
			send.send_text(self.number, "Hello")
		request.assert_not_called()

	def test_send_file_as_image_and_attach_it(self):
		self.incoming({"type": "text", "text": {"body": "Send a photo"}})
		self.open_window()
		file_doc = frappe.get_doc(
			{"doctype": "File", "file_name": "kurta.png", "content": b"\x89PNG\r\n", "is_private": 1}
		).insert(ignore_permissions=True)
		with patch(REQUESTS, return_value=graph_response(OK)):
			result = send.send_file(self.number, file_doc.file_url, "Blue kurta")
		message = frappe.get_doc("WhatsApp Message", result["data"]["message"])
		self.assertEqual((message.message_type, message.body), ("image", "Blue kurta"))
		self.assertEqual(frappe.db.get_value("File", file_doc.name, "attached_to_name"), message.name)

	def test_template_starts_a_conversation_with_typed_values(self):
		template = make_template("test_inbox_start", account=self.account)
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			result = send.send_template(self.number, template, json.dumps(["Meera", ""]))
		self.assertTrue(result["status"])
		parameters = request.call_args.kwargs["json"]["template"]["components"][0]["parameters"]
		# The empty second value keeps the template's sample.
		self.assertEqual([p["text"] for p in parameters], ["Meera", "SO-0001"])
		self.assertEqual(self.profile().conversation_status, "Open")

	def test_status_updates_are_published(self):
		name = self.outgoing("wamid.STATUS1")
		with patch("frappe.publish_realtime") as publish:
			self.post(
				"messages",
				{"statuses": [{"id": "wamid.STATUS1", "status": "read", "timestamp": "1761200000"}]},
			)
		self.assertEqual(frappe.db.get_value("WhatsApp Message", name, "status"), "Read")
		event = publish.call_args.args[1]
		self.assertEqual((event["message"], event["event"]), (name, "status"))
