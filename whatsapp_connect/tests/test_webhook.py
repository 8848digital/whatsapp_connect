# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import json
from unittest.mock import patch

import frappe

from whatsapp_connect.tests.utils import sign, webhook_body
from whatsapp_connect.tests.webhook_case import WebhookTestCase
from whatsapp_connect.whatsapp_connect_core.webhook.handler import receive, verify_subscription


class TestWebhookEvents(WebhookTestCase):
	"""Handshake, signature check, statuses and Business-app echoes."""

	def test_handshake(self):
		token = frappe.db.get_value("WhatsApp Account", self.account, "verify_token")
		ok = verify_subscription(
			{"hub.mode": "subscribe", "hub.verify_token": token, "hub.challenge": "12345"}
		)
		self.assertEqual((ok.status_code, ok.get_data(as_text=True)), (200, "12345"))
		bad = verify_subscription(
			{"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "1"}
		)
		self.assertEqual(bad.status_code, 403)

	def test_unsigned_and_forged_calls_are_refused(self):
		logs = frappe.db.count("WhatsApp Log")
		self.assertEqual(self.post("messages", {"messages": []}, signed=False).status_code, 403)
		body = webhook_body(self.account, "messages", {})
		self.assertEqual(receive(body, sign(body, "forged")).status_code, 403)
		self.assertEqual(frappe.db.count("WhatsApp Log"), logs)

	def test_without_secret_unsigned_calls_follow_the_setting(self):
		frappe.db.delete("__Auth", {"doctype": "WhatsApp Account", "fieldname": "app_secret"})
		self.assertEqual(self.post("messages", {"messages": []}, signed=False).status_code, 200)
		frappe.db.set_single_value("WhatsApp Settings", "require_signed_webhooks", 1)
		self.assertEqual(self.post("messages", {"messages": []}, signed=False).status_code, 403)

	def test_unknown_phone_number_id_is_ignored(self):
		body = json.dumps(
			{
				"entry": [
					{
						"changes": [
							{
								"field": "messages",
								"value": {
									"metadata": {"phone_number_id": "unknown"},
									"messages": [
										{"from": self.number, "id": "wamid.LOST", "type": "text", "text": {"body": "x"}}
									],
								},
							}
						]
					}
				]
			}
		).encode()
		self.assertEqual(receive(body, sign(body)).status_code, 200)
		self.assertFalse(frappe.db.exists("WhatsApp Message", {"wamid": "wamid.LOST"}))

	def test_statuses_never_move_back(self):
		name = self.outgoing("wamid.S1")
		self.post(
			"messages", {"statuses": [{"id": "wamid.S1", "status": "read", "timestamp": "1761200100"}]}
		)
		self.post(
			"messages",
			{
				"statuses": [
					{
						"id": "wamid.S1",
						"status": "delivered",
						"timestamp": "1761200050",
						"pricing": {"category": "utility"},
					}
				]
			},
		)
		row = frappe.db.get_value(
			"WhatsApp Message",
			name,
			["status", "read_at", "delivered_at", "pricing_category"],
			as_dict=True,
		)
		self.assertEqual((row.status, row.pricing_category), ("Read", "utility"))
		self.assertTrue(row.read_at and row.delivered_at)

	def test_failed_status_keeps_the_reason(self):
		name = self.outgoing("wamid.F1")
		errors = [
			{"code": 131026, "title": "Message undeliverable", "error_data": {"details": "Not on WhatsApp"}}
		]
		self.post("messages", {"statuses": [{"id": "wamid.F1", "status": "failed", "errors": errors}]})
		row = frappe.db.get_value(
			"WhatsApp Message", name, ["status", "error_code", "error_message"], as_dict=True
		)
		self.assertEqual(
			(row.status, row.error_code, row.error_message),
			("Failed", "131026", "Message undeliverable - Not on WhatsApp"),
		)

	def test_status_for_unknown_message_is_ignored(self):
		self.assertEqual(
			self.post("messages", {"statuses": [{"id": "wamid.ELSEWHERE", "status": "read"}]}).status_code,
			200,
		)

	def test_business_app_echo_is_saved_without_sending(self):
		echo = {
			"from": "15550000000",
			"to": self.number,
			"id": "wamid.ECHO1",
			"timestamp": "1761200000",
			"type": "text",
			"text": {"body": "From the phone"},
		}
		with patch(
			"whatsapp_connect.whatsapp_connect_core.cloud_api.client.requests.request"
		) as request:
			self.post("smb_message_echoes", {"message_echoes": [echo]})
			self.post("smb_message_echoes", {"message_echoes": [echo]})
		request.assert_not_called()
		rows = frappe.get_all(
			"WhatsApp Message",
			filters={"wamid": "wamid.ECHO1"},
			fields=["direction", "status", "body", "source"],
		)
		self.assertEqual(len(rows), 1)
		self.assertEqual(
			(rows[0].direction, rows[0].status, rows[0].body, rows[0].source),
			("Outgoing", "Sent", "From the phone", "WhatsApp Business App"),
		)
