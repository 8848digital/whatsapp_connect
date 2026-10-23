# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Base class for webhook tests: a signed webhook call for one change."""

import json
from unittest.mock import patch

import frappe

from whatsapp_connect.tests.utils import (
	APP_SECRET,
	IntegrationTestCase,
	make_account,
	random_number,
	sign,
	webhook_body,
)
from whatsapp_connect.whatsapp_connect_core.webhook.handler import receive

ENQUEUE = "whatsapp_connect.whatsapp_connect_core.webhook.incoming.frappe.enqueue"


class WebhookTestCase(IntegrationTestCase):
	"""One account with an App Secret, and helpers to post webhook calls."""

	def setUp(self):
		"""Use one account with an App Secret; other accounts' secrets are cleared (rolled back)."""
		frappe.db.delete("__Auth", {"doctype": "WhatsApp Account", "fieldname": "app_secret"})
		self.account = make_account("Test Webhook Account", app_secret=APP_SECRET)
		self.number = random_number()

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def post(self, field: str, value: dict, signed: bool = True):
		"""Send a signed webhook call for one change; background jobs are not started."""
		body = webhook_body(self.account, field, value)
		with patch(ENQUEUE) as enqueue:
			response = receive(body, sign(body) if signed else None)
		self.enqueue = enqueue
		return response

	def incoming(self, message: dict, name: str = "Asha"):
		"""Post one incoming message from the test number and return the saved message."""
		message = {
			"from": self.number,
			"id": f"wamid.{frappe.generate_hash(length=10)}",
			"timestamp": "1761200000",
			**message,
		}
		self.post(
			"messages",
			{"contacts": [{"wa_id": self.number, "profile": {"name": name}}], "messages": [message]},
		)
		return frappe.get_doc("WhatsApp Message", {"wamid": message["id"]})

	def outgoing(self, wamid: str) -> str:
		"""Insert a sent message (not sent to Meta) and return its name."""
		message = frappe.get_doc(
			{
				"doctype": "WhatsApp Message",
				"phone_number": self.number,
				"body": "x",
				"whatsapp_account": self.account,
				"status": "Sent",
				"wamid": wamid,
			}
		)
		message.flags.skip_send = True
		return message.insert(ignore_permissions=True).name
