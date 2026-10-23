# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe

from whatsapp_connect.tests.utils import REQUESTS, graph_response
from whatsapp_connect.tests.webhook_case import WebhookTestCase
from whatsapp_connect.whatsapp_connect_automation import auto_reply, erp_actions

OK = {"messages": [{"id": "wamid.AUTO"}]}
IS_OPEN = "whatsapp_connect.whatsapp_connect_automation.rules.is_open"
ACTIONS = "whatsapp_connect.whatsapp_connect_automation.actions"
RULE_UTILS = (
	"whatsapp_connect.whatsapp_connect_automation.doctype.whatsapp_auto_reply.auto_reply_utils"
)


class TestAutoReply(WebhookTestCase):
	"""WhatsApp Auto Reply rules answer incoming messages."""

	def setUp(self):
		"""Remove other rules (rolled back) and keep the business open."""
		super().setUp()
		frappe.db.delete("WhatsApp Auto Reply")
		patcher = patch(IS_OPEN, return_value=True)
		self.is_open = patcher.start()
		self.addCleanup(patcher.stop)

	def make_rule(self, title: str, **values) -> str:
		"""Insert an enabled rule with a text reply."""
		rule = frappe.get_doc(
			{
				"doctype": "WhatsApp Auto Reply",
				"title": f"{title} {frappe.generate_hash(length=5)}",
				"trigger": "Keyword",
				"reply_type": "Text",
				"reply_text": f"Answer of {title}",
				**values,
			}
		).insert(ignore_permissions=True)
		return rule.name

	def answers(self, message: dict) -> list[dict]:
		"""Post a message, run the queued auto-reply job, and return the payloads sent to Meta."""
		self.incoming({"from": self.number, **message})
		jobs = [
			call
			for call in self.enqueue.call_args_list
			if call.args and call.args[0] == auto_reply.SEND_JOB
		]
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			for job in jobs:
				auto_reply.send_auto_replies(job.kwargs["message_name"], job.kwargs["rules"])
		return [call.kwargs["json"] for call in request.call_args_list]

	def text(self, body: str) -> dict:
		"""Return a text message object."""
		return {"type": "text", "text": {"body": body}}

	def test_keyword_answers_with_text(self):
		self.make_rule("Hours", keywords="hours\ntimings")
		sent = self.answers(self.text("Timings?"))
		self.assertEqual([payload["text"]["body"] for payload in sent], [f"Answer of Hours"])
		reply = frappe.get_last_doc(
			"WhatsApp Message", {"phone_number": self.number, "direction": "Outgoing"}
		)
		self.assertTrue(reply.source.startswith("Auto Reply: Hours"))

	def test_match_types(self):
		self.make_rule("Price", keywords="price", match_type="Contains")
		self.make_rule("Order", keywords="order", match_type="Starts With")
		self.assertEqual(
			self.answers(self.text("What is the price of the kurta"))[0]["text"]["body"], "Answer of Price"
		)
		self.assertEqual(
			self.answers(self.text("Order SO-0001 status"))[0]["text"]["body"], "Answer of Order"
		)
		self.assertEqual(self.answers(self.text("hello there")), [])

	def test_buttons_and_button_reply(self):
		self.make_rule(
			"Menu",
			keywords="menu",
			reply_type="Buttons or List",
			options=[{"title": "Order status"}, {"title": "Talk to us", "option_id": "agent"}],
		)
		self.make_rule("Agent", trigger="Button Reply", keywords="agent")
		menu = self.answers(self.text("Menu"))[0]["interactive"]
		self.assertEqual(
			[button["reply"]["id"] for button in menu["action"]["buttons"]], ["order_status", "agent"]
		)
		tap = {
			"type": "interactive",
			"interactive": {"type": "button_reply", "button_reply": {"id": "agent", "title": "Talk to us"}},
		}
		self.assertEqual(self.answers(tap)[0]["text"]["body"], "Answer of Agent")

	def test_welcome_and_away_answer_together_without_a_keyword(self):
		self.make_rule("Welcome", trigger="First Message")
		self.make_rule("Away", trigger="Outside Business Hours")
		self.make_rule("Fallback", trigger="Any Other Message")
		self.is_open.return_value = False
		bodies = [payload["text"]["body"] for payload in self.answers(self.text("Hi"))]
		self.assertEqual(bodies, ["Answer of Welcome", "Answer of Away"])

		self.is_open.return_value = True
		bodies = [payload["text"]["body"] for payload in self.answers(self.text("Hello again"))]
		self.assertEqual(bodies, ["Answer of Fallback"])

	def test_cooldown_and_assigned_conversation(self):
		self.make_rule("Away", trigger="Outside Business Hours", cooldown_minutes=60)
		self.is_open.return_value = False
		self.assertEqual(len(self.answers(self.text("Hi"))), 1)
		self.assertEqual(self.answers(self.text("Anyone?")), [])

		self.make_rule("Thanks", keywords="thanks")
		frappe.db.set_value("WhatsApp Profile", self.number, "assigned_to", "Administrator")
		self.assertEqual(self.answers(self.text("Thanks")), [])

	def test_stop_is_not_answered(self):
		self.make_rule("Fallback", trigger="Any Other Message")
		self.assertEqual(self.answers(self.text("STOP")), [])

	def test_action_reply(self):
		actions = {"Echo": "whatsapp_connect.whatsapp_connect_automation.test_auto_reply.echo_action"}
		with patch(f"{ACTIONS}.get_actions", return_value=actions), patch(
			f"{RULE_UTILS}.get_actions", return_value=actions
		):
			self.make_rule(
				"Echo", keywords="balance", reply_type="Action", action="Echo", reply_text="Hello"
			)
			sent = self.answers(self.text("balance"))
		self.assertEqual(sent[0]["text"]["body"], "Hello\n\nYou wrote: balance")

	def test_unknown_action_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self.make_rule("Bad", keywords="x", reply_type="Action", action="Missing Action")

	def test_erp_actions_need_a_customer(self):
		message = self.incoming(self.text("balance"))
		self.assertEqual(erp_actions.outstanding_balance(message), erp_actions.NOT_FOUND)
		self.assertEqual(erp_actions.order_status(message), erp_actions.NOT_FOUND)

	def test_customer_is_found_through_the_contact(self):
		if not frappe.db.exists("DocType", "Customer"):
			self.skipTest("ERPNext is not installed")
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": f"Asha {frappe.generate_hash(length=5)}",
				"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}),
				"territory": frappe.db.get_value("Territory", {"is_group": 0}),
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Asha",
				"phone_nos": [{"phone": f"+{self.number}"}],
				"links": [{"link_doctype": "Customer", "link_name": customer.name}],
			}
		).insert(ignore_permissions=True)
		message = self.incoming(self.text("balance"))
		self.assertEqual(erp_actions.get_customer(message), customer.name)
		self.assertEqual(erp_actions.outstanding_balance(message), "You have nothing to pay. Thank you.")


def echo_action(message) -> str:
	"""Test action: repeat the message."""
	return f"You wrote: {message.body}"
