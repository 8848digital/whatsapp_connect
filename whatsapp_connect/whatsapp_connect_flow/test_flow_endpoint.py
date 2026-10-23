# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import base64
import json
import os
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import frappe

from whatsapp_connect.tests.utils import (
	APP_SECRET,
	REQUESTS,
	IntegrationTestCase,
	graph_response,
	make_account,
	random_number,
	sign,
	webhook_body,
)
from whatsapp_connect.whatsapp_connect_core.webhook.handler import receive
from whatsapp_connect.whatsapp_connect_flow.doctype.whatsapp_flow.test_whatsapp_flow import (
	make_flow,
)
from whatsapp_connect.whatsapp_connect_flow.endpoint import handle_request
from whatsapp_connect.whatsapp_connect_flow.keys import generate_flow_keys

OAEP = padding.OAEP(
	mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
)


class TestFlowEndpointAndAnswers(IntegrationTestCase):
	"""The encrypted data endpoint, keys and saved answers."""

	def setUp(self):
		"""One account with an App Secret and Flow keys; a flow sent to a number."""
		frappe.db.delete(
			"__Auth",
			{"doctype": "WhatsApp Account", "fieldname": ["in", ["app_secret", "flow_private_key"]]},
		)
		self.account = make_account("Test Flow Account", app_secret=APP_SECRET)
		with patch(REQUESTS, return_value=graph_response({"success": True})) as request:
			self.public_key = generate_flow_keys(self.account)
		self.assertTrue(request.call_args.args[1].endswith("/whatsapp_business_encryption"))
		self.flow = make_flow(whatsapp_account=self.account, use_endpoint=1, target_doctype="Contact")
		frappe.db.set_value("WhatsApp Flow", self.flow.name, "meta_flow_id", "flow-7")
		self.token = f"token-{frappe.generate_hash(length=8)}"
		message = frappe.get_doc(
			{
				"doctype": "WhatsApp Message",
				"message_type": "flow",
				"phone_number": random_number(),
				"whatsapp_account": self.account,
				"payload": json.dumps({"flow": self.flow.name, "flow_token": self.token}),
				"status": "Sent",
			}
		)
		message.flags.skip_send = True
		message.insert(ignore_permissions=True)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def call(self, data, public_key=None, signed=True):
		"""Encrypt a request like Meta, call the endpoint, and decrypt the answer."""
		aes_key, iv = os.urandom(16), os.urandom(16)
		key = serialization.load_pem_public_key((public_key or self.public_key).encode())
		body = json.dumps(
			{
				"encrypted_flow_data": base64.b64encode(
					AESGCM(aes_key).encrypt(iv, json.dumps(data).encode(), None)
				).decode(),
				"encrypted_aes_key": base64.b64encode(key.encrypt(aes_key, OAEP)).decode(),
				"initial_vector": base64.b64encode(iv).decode(),
			}
		).encode()
		response = handle_request(body, sign(body) if signed else None)
		if response.status_code != 200:
			return response.status_code, None
		flipped = bytes(byte ^ 0xFF for byte in iv)
		return 200, json.loads(
			AESGCM(aes_key).decrypt(flipped, base64.b64decode(response.get_data()), None)
		)

	def test_health_check(self):
		self.assertEqual(
			self.call({"version": "3.0", "action": "ping"}), (200, {"data": {"status": "active"}})
		)

	def test_screens_move_on_and_complete(self):
		self.assertEqual(
			self.call({"action": "INIT", "flow_token": self.token})[1], {"screen": "DETAILS", "data": {}}
		)
		answer = self.call(
			{
				"action": "data_exchange",
				"screen": "DETAILS",
				"flow_token": self.token,
				"data": {"first_name": "Asha"},
			}
		)[1]
		self.assertEqual(answer, {"screen": "TOPIC", "data": {"first_name": "Asha"}})
		final = self.call(
			{
				"action": "data_exchange",
				"screen": "TOPIC",
				"flow_token": self.token,
				"data": {"topic": "sales"},
			}
		)[1]
		self.assertEqual(final["screen"], "SUCCESS")
		self.assertEqual(
			final["data"]["extension_message_response"]["params"],
			{"flow_token": self.token, "topic": "sales"},
		)

	def test_error_notice_is_acknowledged(self):
		self.assertEqual(
			self.call({"action": "data_exchange", "data": {"error": "invalid", "error_message": "x"}})[1],
			{"data": {"acknowledged": True}},
		)

	def test_custom_handler(self):
		real_get_hooks = frappe.get_hooks
		handlers = {self.flow.name: ["frappe.utils.cstr"]}

		def get_hooks(hook=None, default=None, *args, **kwargs):
			"""Answer only for the flow handler hook; everything else is unchanged."""
			if hook == "whatsapp_connect_flow_handlers":
				return handlers
			return real_get_hooks(hook, default, *args, **kwargs)

		with patch("frappe.get_hooks", side_effect=get_hooks), patch(
			"frappe.utils.cstr", return_value={"screen": "CUSTOM", "data": {}}
		):
			self.assertEqual(
				self.call({"action": "INIT", "flow_token": self.token})[1], {"screen": "CUSTOM", "data": {}}
			)

	def test_unknown_key_and_bad_signature(self):
		from whatsapp_connect.whatsapp_connect_flow.crypto import generate_key_pair

		_private, other_public = generate_key_pair()
		self.assertEqual(self.call({"action": "ping"}, public_key=other_public)[0], 421)
		self.assertEqual(self.call({"action": "ping"}, signed=False)[0], 403)

	def test_answers_create_a_document(self):
		answers = {
			"flow_token": self.token,
			"first_name": "Flow",
			"email": f"{frappe.generate_hash(length=6)}@example.com",
		}
		value = {
			"contacts": [{"wa_id": "919900000001", "profile": {"name": "Asha"}}],
			"messages": [
				{
					"from": random_number(),
					"id": f"wamid.{frappe.generate_hash(length=8)}",
					"type": "interactive",
					"interactive": {
						"type": "nfm_reply",
						"nfm_reply": {"response_json": json.dumps(answers), "body": "Sent"},
					},
				}
			],
		}
		body = webhook_body(self.account, "messages", value)
		with patch("whatsapp_connect.whatsapp_connect_core.webhook.incoming.frappe.enqueue"), patch(
			"whatsapp_connect.whatsapp_connect_flow.responses.frappe.publish_realtime"
		) as realtime:
			self.assertEqual(receive(body, sign(body)).status_code, 200)
		response = frappe.get_last_doc("WhatsApp Flow Response", filters={"flow_token": self.token})
		self.assertEqual(
			(response.flow, response.reference_doctype), (self.flow.name, "Contact"), response.error
		)
		self.assertEqual(
			frappe.db.get_value("Contact", response.reference_name, "designation"), answers["email"]
		)
		self.assertEqual(realtime.call_args.args[0], "whatsapp_flow_response")
