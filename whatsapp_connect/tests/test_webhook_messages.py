# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import json

import frappe

from whatsapp_connect.tests.webhook_case import WebhookTestCase
from whatsapp_connect.whatsapp_connect_core.messaging.opt_out import is_opted_out


class TestWebhookMessages(WebhookTestCase):
	"""Every incoming message type."""

	def test_text_message(self):
		message = self.incoming({"type": "text", "text": {"body": "Hello"}})
		self.assertEqual(
			(message.direction, message.status, message.body, message.message_type),
			("Incoming", "Received", "Hello", "text"),
		)
		profile = frappe.get_doc("WhatsApp Profile", self.number)
		self.assertEqual(profile.profile_name, "Asha")
		self.assertTrue(profile.last_incoming_at)

	def test_duplicate_delivery_is_skipped(self):
		value = {
			"messages": [{"from": self.number, "id": "wamid.DUP1", "type": "text", "text": {"body": "x"}}]
		}
		self.post("messages", value)
		self.post("messages", value)
		self.assertEqual(frappe.db.count("WhatsApp Message", {"wamid": "wamid.DUP1"}), 1)

	def test_media_is_downloaded_in_background(self):
		message = self.incoming(
			{"type": "image", "image": {"id": "media-9", "mime_type": "image/jpeg", "caption": "Photo"}}
		)
		self.assertEqual(
			(message.media_id, message.mime_type, message.body), ("media-9", "image/jpeg", "Photo")
		)
		self.assertTrue(self.enqueue.call_args.args[0].endswith("save_incoming_media"))

	def test_reaction_and_reply_context(self):
		reaction = self.incoming(
			{"type": "reaction", "reaction": {"message_id": "wamid.OUT", "emoji": "❤️"}}
		)
		self.assertEqual((reaction.reaction_emoji, reaction.reply_to_wamid), ("❤️", "wamid.OUT"))
		reply = self.incoming({"type": "text", "text": {"body": "yes"}, "context": {"id": "wamid.ASK"}})
		self.assertEqual(reply.reply_to_wamid, "wamid.ASK")

	def test_button_and_list_replies(self):
		button = self.incoming(
			{
				"type": "interactive",
				"interactive": {"type": "button_reply", "button_reply": {"id": "yes", "title": "Yes"}},
			}
		)
		self.assertEqual((button.body, json.loads(button.payload)["id"]), ("Yes", "yes"))
		row = self.incoming(
			{
				"type": "interactive",
				"interactive": {"type": "list_reply", "list_reply": {"id": "r2", "title": "Row 2"}},
			}
		)
		self.assertEqual(row.body, "Row 2")

	def test_flow_answers(self):
		answers = {"name": "Asha", "date": "2026-10-30"}
		message = self.incoming(
			{
				"type": "interactive",
				"interactive": {
					"type": "nfm_reply",
					"nfm_reply": {"response_json": json.dumps(answers), "body": "Sent"},
				},
			}
		)
		self.assertEqual((message.message_type, json.loads(message.payload)), ("flow", answers))

	def test_order_location_and_unknown_types(self):
		order = self.incoming(
			{
				"type": "order",
				"order": {"catalog_id": "c1", "product_items": [{"product_retailer_id": "p1"}]},
			}
		)
		self.assertEqual(json.loads(order.payload)["catalog_id"], "c1")
		location = self.incoming(
			{"type": "location", "location": {"latitude": 12.9, "longitude": 77.5, "name": "Office"}}
		)
		self.assertIn("Office", location.body)
		unknown = self.incoming({"type": "something_new", "something_new": {}})
		self.assertEqual(unknown.message_type, "unsupported")

	def test_stop_opts_out(self):
		self.incoming({"type": "text", "text": {"body": "STOP"}})
		self.assertTrue(is_opted_out(self.number))
