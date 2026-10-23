# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Answer incoming messages with the WhatsApp Auto Reply rules."""

import json

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_automation.actions import run_action
from whatsapp_connect.whatsapp_connect_automation.rules import find_rules, source_of
from whatsapp_connect.whatsapp_connect_core.messaging.opt_out import (
	OPT_IN_KEYWORDS,
	OPT_OUT_KEYWORDS,
)
from whatsapp_connect.whatsapp_connect_core.messaging.template_send import send_template
from whatsapp_connect.whatsapp_connect_flow.sending import send_flow

# Answers to these are not useful: emoji reactions, Flow answers, unknown types.
SKIPPED_TYPES = ("reaction", "flow", "unsupported")
SEND_JOB = "whatsapp_connect.whatsapp_connect_automation.auto_reply.send_auto_replies"


def handle_incoming(message) -> None:
	"""
	Choose the rules that answer a message and send the answers in a background job
	(whatsapp_connect_incoming_handlers hook), so the webhook answers Meta quickly.

	Parameters:
	        message (Document, required): The saved incoming WhatsApp Message.

	Returns:
	        None
	"""
	if message.message_type in SKIPPED_TYPES or __is_opt_keyword(message.body):
		return
	if frappe.db.get_single_value("WhatsApp Auto Reply Settings", "paused"):
		return
	assigned = bool(frappe.db.get_value("WhatsApp Profile", message.profile, "assigned_to"))
	rules = find_rules(message, assigned)
	if rules:
		frappe.enqueue(SEND_JOB, message_name=message.name, rules=rules, enqueue_after_commit=True)


def send_auto_replies(message_name: str, rules: list[str]) -> None:
	"""
	Send the answer of each rule to the number that wrote (background job).

	A failed answer is logged; the next rule still answers.

	Parameters:
	        message_name (str, required): The incoming WhatsApp Message.
	        rules (list[str], required): WhatsApp Auto Reply names, in order.

	Returns:
	        None
	"""
	message = frappe.get_doc("WhatsApp Message", message_name)
	for rule_name in rules:
		try:
			send_rule(frappe.get_doc("WhatsApp Auto Reply", rule_name), message)
		except Exception:
			frappe.log_error(title=_("WhatsApp auto-reply {0} failed").format(rule_name))


def send_rule(rule, message):
	"""
	Send one rule's answer to the sender of a message.

	Parameters:
	        rule (Document, required): The WhatsApp Auto Reply.
	        message (Document, required): The incoming WhatsApp Message.

	Returns:
	        Document: The outgoing WhatsApp Message.
	"""
	source = source_of(rule.name)
	if rule.reply_type == "Template":
		return send_template(
			rule.template, message.phone_number, account=message.whatsapp_account, source=source
		)
	if rule.reply_type == "Flow":
		reply = send_flow(rule.flow, message.phone_number, text=rule.reply_text)
		reply.db_set("source", source)
		return reply

	values = {"message_type": "text", "body": rule.reply_text}
	if rule.reply_type == "Buttons or List":
		values = {
			"message_type": "interactive",
			"body": rule.reply_text,
			"interactive_options": json.dumps(
				[
					{"id": row.option_id, "title": row.title, "description": row.description or ""}
					for row in rule.options
				]
			),
			"list_button_label": rule.list_button_label,
		}
	elif rule.reply_type == "Action":
		result = run_action(rule.action, message)
		values["body"] = "\n\n".join(part for part in (rule.reply_text, result) if part)
	return __send(message, source, values)


def __send(message, source: str, values: dict):
	"""
	Insert (and so send) an outgoing message to the sender, linked to the same record.

	Parameters:
	        message (Document, required): The incoming WhatsApp Message.
	        source (str, required): "Auto Reply: <rule>".
	        values (dict, required): Content fields of the reply.

	Returns:
	        Document: The outgoing WhatsApp Message.
	"""
	reply = frappe.get_doc(
		{
			"doctype": "WhatsApp Message",
			"direction": "Outgoing",
			"phone_number": message.phone_number,
			"whatsapp_account": message.whatsapp_account,
			"reference_doctype": message.reference_doctype,
			"reference_name": message.reference_name,
			"source": source,
			**values,
		}
	)
	reply.insert(ignore_permissions=True)
	return reply


def __is_opt_keyword(text: str | None) -> bool:
	"""
	Tell if a message is STOP or START, which the opt-out feature answers instead.

	Parameters:
	        text (str, optional): The message text.

	Returns:
	        bool: True for an opt-out or opt-in keyword.
	"""
	keyword = (text or "").strip().lower().rstrip(".!")
	return keyword in OPT_OUT_KEYWORDS or keyword in OPT_IN_KEYWORDS
