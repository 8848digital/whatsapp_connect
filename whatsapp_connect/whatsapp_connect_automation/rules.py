# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Choose the WhatsApp Auto Reply rules that answer an incoming message."""

import json

import frappe
from frappe.utils import add_to_date, now_datetime

from whatsapp_connect.whatsapp_connect_automation.business_hours import is_open
from whatsapp_connect.whatsapp_connect_automation.doctype.whatsapp_auto_reply.auto_reply_utils import (
	split_keywords,
)

RULE_FIELDS = [
	"name",
	"trigger",
	"match_type",
	"keywords",
	"cooldown_minutes",
	"skip_when_assigned",
]
BUTTON_TYPES = ("interactive", "button")


def find_rules(message, assigned: bool) -> list[str]:
	"""
	Return the rules that answer a message, in the order to send them.

	A keyword or button rule answers alone. Without one, the welcome rule (first
	message) and the away rule (outside business hours) both answer. When none of
	these match, the "Any Other Message" rule answers.

	Parameters:
	        message (Document, required): The incoming WhatsApp Message.
	        assigned (bool, required): True when an agent has the conversation.

	Returns:
	        list[str]: WhatsApp Auto Reply names; empty when nothing answers.
	"""
	rules = [
		rule
		for rule in __enabled_rules(message.whatsapp_account)
		if not (assigned and rule.skip_when_assigned)
	]
	by_trigger = {}
	for rule in rules:
		by_trigger.setdefault(rule.trigger, []).append(rule)

	if message.message_type in BUTTON_TYPES:
		chosen = __first(by_trigger.get("Button Reply"), lambda rule: __button_matches(rule, message))
	else:
		chosen = __first(by_trigger.get("Keyword"), lambda rule: __keyword_matches(rule, message.body))
	if chosen:
		return __not_cooling(message, [chosen])

	chosen = []
	if __is_first_message(message):
		chosen += by_trigger.get("First Message", [])[:1]
	if not is_open():
		chosen += by_trigger.get("Outside Business Hours", [])[:1]
	if not chosen:
		chosen = by_trigger.get("Any Other Message", [])[:1]
	return __not_cooling(message, chosen)


def __enabled_rules(account: str | None) -> list:
	"""
	Return the enabled rules for an account, highest priority first.

	Parameters:
	        account (str, optional): The receiving WhatsApp Account.

	Returns:
	        list: Rule rows with RULE_FIELDS.
	"""
	or_filters = [["whatsapp_account", "is", "not set"]]
	if account:
		or_filters.append(["whatsapp_account", "=", account])
	return frappe.get_all(
		"WhatsApp Auto Reply",
		filters={"enabled": 1},
		or_filters=or_filters,
		fields=RULE_FIELDS,
		order_by="priority desc, creation asc",
	)


def __first(rules: list | None, matches) -> object | None:
	"""
	Return the first rule that matches.

	Parameters:
	        rules (list, optional): Candidate rules.
	        matches (callable, required): Test for one rule.

	Returns:
	        object | None: The rule row.
	"""
	return next((rule for rule in rules or [] if matches(rule)), None)


def __keyword_matches(rule, text: str | None) -> bool:
	"""
	Tell if a message text matches one of the rule's keywords.

	Parameters:
	        rule (dict, required): A Keyword rule.
	        text (str, optional): The message text.

	Returns:
	        bool: True on a match.
	"""
	text = (text or "").strip().lower().rstrip(".!?")
	if not text:
		return False
	keywords = split_keywords(rule.keywords)
	if rule.match_type == "Contains":
		return any(keyword in text for keyword in keywords)
	if rule.match_type == "Starts With":
		return any(text.startswith(keyword) for keyword in keywords)
	return text in keywords


def __button_matches(rule, message) -> bool:
	"""
	Tell if a button or list reply has one of the rule's IDs or texts.

	Parameters:
	        rule (dict, required): A Button Reply rule.
	        message (Document, required): The incoming button or list reply.

	Returns:
	        bool: True on a match.
	"""
	try:
		payload = json.loads(message.payload or "{}")
	except ValueError:
		payload = {}
	values = {
		str(payload.get(key) or "").strip().lower() for key in ("id", "payload", "title", "text")
	}
	values.add((message.body or "").strip().lower())
	return bool(values & set(split_keywords(rule.keywords)))


def __is_first_message(message) -> bool:
	"""
	Tell if this is the first message the number ever sent.

	Parameters:
	        message (Document, required): The incoming WhatsApp Message.

	Returns:
	        bool: True for the first incoming message.
	"""
	return (
		frappe.db.count(
			"WhatsApp Message", {"phone_number": message.phone_number, "direction": "Incoming"}
		)
		<= 1
	)


def __not_cooling(message, rules: list) -> list[str]:
	"""
	Drop the rules that answered this number less than their cooldown ago.

	Parameters:
	        message (Document, required): The incoming WhatsApp Message.
	        rules (list, required): Chosen rule rows.

	Returns:
	        list[str]: Names of the rules that may answer.
	"""
	names = []
	for rule in rules:
		minutes = rule.cooldown_minutes or 0
		recent = minutes and frappe.db.exists(
			"WhatsApp Message",
			{
				"phone_number": message.phone_number,
				"source": source_of(rule.name),
				"creation": [">=", add_to_date(now_datetime(), minutes=-minutes)],
			},
		)
		if not recent:
			names.append(rule.name)
	return names


def source_of(rule: str) -> str:
	"""
	Return the source text of messages sent by a rule.

	Parameters:
	        rule (str, required): The WhatsApp Auto Reply name.

	Returns:
	        str: "Auto Reply: <rule>".
	"""
	return f"Auto Reply: {rule}"
