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
from whatsapp_connect.whatsapp_connect_flow.doctype.whatsapp_flow import flow_meta
from whatsapp_connect.whatsapp_connect_flow.sending import send_flow

DOWNLOAD = "whatsapp_connect.whatsapp_connect_flow.flow_api.requests.get"


def make_flow(name=None, **values):
	"""Create a two-screen lead flow (Meta is not called)."""
	return frappe.get_doc(
		{
			"doctype": "WhatsApp Flow",
			"flow_name": name or f"Test flow {frappe.generate_hash(length=6)}",
			"whatsapp_account": make_account(),
			"category": "LEAD_GENERATION",
			"screens": [
				{"screen_id": "DETAILS", "title": "Your details"},
				{"screen_id": "TOPIC", "title": "Topic", "footer_label": "Send"},
			],
			"components": [
				{"screen_id": "DETAILS", "component_type": "TextHeading", "label": "Tell us about you"},
				{
					"screen_id": "DETAILS",
					"component_type": "TextInput",
					"field_name": "first_name",
					"label": "Name",
					"required": 1,
					"helper_text": "As on your ID",
				},
				{
					"screen_id": "DETAILS",
					"component_type": "TextInput",
					"field_name": "email",
					"label": "Email",
					"input_type": "email",
					"target_field": "designation",
				},
				{
					"screen_id": "TOPIC",
					"component_type": "RadioButtonsGroup",
					"field_name": "topic",
					"label": "Topic",
					"choices": "sales|Sales\nSupport",
				},
				{
					"screen_id": "TOPIC",
					"component_type": "OptIn",
					"field_name": "consent",
					"label": "I agree",
					"required": 1,
				},
			],
			**values,
		}
	).insert(ignore_permissions=True)


class TestWhatsAppFlow(IntegrationTestCase):
	"""Flow JSON, validation, Meta lifecycle and sending."""

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_flow_json(self):
		flow_json = json.loads(make_flow().flow_json)
		details, topic = flow_json["screens"]
		self.assertEqual(flow_json["version"], "6.0")
		self.assertNotIn("data_api_version", flow_json)
		form = details["layout"]["children"][0]["children"]
		self.assertEqual(
			form[1],
			{
				"type": "TextInput",
				"name": "first_name",
				"label": "Name",
				"required": True,
				"input-type": "text",
				"helper-text": "As on your ID",
			},
		)
		footer = form[-1]
		self.assertEqual(footer["on-click-action"]["name"], "navigate")
		self.assertEqual(footer["on-click-action"]["next"], {"type": "screen", "name": "TOPIC"})
		self.assertEqual(
			footer["on-click-action"]["payload"],
			{"first_name": "${form.first_name}", "email": "${form.email}"},
		)
		self.assertEqual(topic["data"]["first_name"], {"type": "string", "__example__": ""})
		self.assertTrue(topic["terminal"])
		topic_form = topic["layout"]["children"][0]["children"]
		self.assertEqual(
			topic_form[0]["data-source"],
			[{"id": "sales", "title": "Sales"}, {"id": "support", "title": "Support"}],
		)
		complete = topic_form[-1]
		self.assertEqual((complete["label"], complete["on-click-action"]["name"]), ("Send", "complete"))
		self.assertEqual(complete["on-click-action"]["payload"]["first_name"], "${data.first_name}")
		self.assertEqual(complete["on-click-action"]["payload"]["consent"], "${form.consent}")

	def test_endpoint_flow_uses_data_exchange(self):
		flow_json = json.loads(make_flow(use_endpoint=1).flow_json)
		self.assertEqual(flow_json["data_api_version"], "3.0")
		footer = flow_json["screens"][0]["layout"]["children"][0]["children"][-1]
		self.assertEqual(footer["on-click-action"]["name"], "data_exchange")

	def test_validation(self):
		for change in (
			{"screens": [{"screen_id": "bad id", "title": "x"}], "components": []},
			{"components": [{"screen_id": "NOPE", "component_type": "TextBody", "label": "x"}]},
			{
				"components": [
					{
						"screen_id": "DETAILS",
						"component_type": "TextInput",
						"field_name": "Bad Name",
						"label": "x",
					}
				]
			},
			{
				"components": [
					{"screen_id": "DETAILS", "component_type": "Dropdown", "field_name": "pick", "label": "x"}
				]
			},
			{"edit_json": 1, "flow_json": "{not json"},
		):
			with self.assertRaises(frappe.ValidationError):
				make_flow(**change)

	def test_save_to_meta_and_publish(self):
		flow = make_flow()
		answers = [
			graph_response({"id": "flow-1"}),
			graph_response({"success": True, "validation_errors": []}),
			graph_response(
				{"id": "flow-1", "status": "DRAFT", "preview": {"preview_url": "https://preview"}}
			),
		]
		with patch(REQUESTS, side_effect=answers) as request:
			self.assertEqual(flow_meta.save_to_meta(flow.name), [])
		upload = request.call_args_list[1]
		self.assertTrue(upload.args[1].endswith("/flow-1/assets"))
		self.assertEqual(upload.kwargs["data"]["asset_type"], "FLOW_JSON")
		flow.reload()
		self.assertEqual(
			(flow.meta_flow_id, flow.status, flow.preview_url), ("flow-1", "Draft", "https://preview")
		)

		with patch(
			REQUESTS,
			side_effect=[
				graph_response({"success": True}),
				graph_response({"id": "flow-1", "status": "PUBLISHED"}),
			],
		):
			self.assertEqual(flow_meta.publish(flow.name), "Published")

	def test_validation_errors_from_meta_are_kept(self):
		flow = make_flow()
		errors = [
			{
				"error": "INVALID_PROPERTY",
				"error_type": "JSON_SCHEMA_ERROR",
				"message": "Property x is not allowed",
				"line_start": 4,
			}
		]
		answers = [
			graph_response({"id": "flow-2"}),
			graph_response({"success": True, "validation_errors": errors}),
			graph_response({"id": "flow-2", "status": "DRAFT", "validation_errors": errors}),
		]
		with patch(REQUESTS, side_effect=answers):
			self.assertEqual(len(flow_meta.save_to_meta(flow.name)), 1)
		self.assertIn(
			"Property x is not allowed",
			frappe.db.get_value("WhatsApp Flow", flow.name, "validation_errors"),
		)

	def test_actions_need_a_meta_flow(self):
		with self.assertRaises(frappe.ValidationError):
			flow_meta.publish(make_flow().name)

	def test_import_from_meta(self):
		account = make_account()
		meta_json = {
			"version": "6.0",
			"screens": [
				{"id": "ONE", "title": "One", "layout": {"type": "SingleColumnLayout", "children": []}}
			],
		}
		download = graph_response(meta_json)
		answers = [
			graph_response(
				{
					"data": [
						{
							"id": "flow-9",
							"name": f"Imported {frappe.generate_hash(length=6)}",
							"status": "PUBLISHED",
							"categories": ["SURVEY"],
						}
					]
				}
			),
			graph_response(
				{
					"data": [{"name": "flow.json", "asset_type": "FLOW_JSON", "download_url": "https://download"}]
				}
			),
		]
		with patch(REQUESTS, side_effect=answers), patch(DOWNLOAD, return_value=download):
			self.assertEqual(flow_meta.import_flows(account), 1)
		flow = frappe.get_doc("WhatsApp Flow", {"meta_flow_id": "flow-9"})
		self.assertEqual((flow.status, flow.category, flow.edit_json), ("Published", "SURVEY", 1))
		self.assertEqual(json.loads(flow.flow_json)["screens"][0]["id"], "ONE")

	def test_send_draft_flow(self):
		flow = make_flow()
		frappe.db.set_value("WhatsApp Flow", flow.name, "meta_flow_id", "flow-3")
		number = random_number()
		with patch(REQUESTS, return_value=graph_response({"messages": [{"id": "wamid.F"}]})) as request:
			message = send_flow(flow.name, number, "Fill this in")
		body = request.call_args.kwargs["json"]
		self.assertEqual((body["type"], body["interactive"]["type"]), ("interactive", "flow"))
		parameters = body["interactive"]["action"]["parameters"]
		self.assertEqual(
			(parameters["flow_id"], parameters["mode"], parameters["flow_action"]),
			("flow-3", "draft", "navigate"),
		)
		self.assertEqual(parameters["flow_action_payload"], {"screen": "DETAILS"})
		self.assertEqual(parameters["flow_token"], json.loads(message.payload)["flow_token"])
		self.assertEqual((message.status, message.message_type), ("Sent", "flow"))
