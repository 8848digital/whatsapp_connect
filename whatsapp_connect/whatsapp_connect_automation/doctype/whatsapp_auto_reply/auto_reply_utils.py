# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Business logic for WhatsApp Auto Reply."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_automation.actions import get_actions

MAX_OPTIONS = 10
KEYWORD_TRIGGERS = ("Keyword", "Button Reply")


def validate_rule(rule) -> None:
	"""
	Refuse a rule that WhatsApp cannot send, and fill the option IDs.

	Parameters:
	        rule (Document, required): The WhatsApp Auto Reply being saved.

	Returns:
	        None
	"""
	if rule.trigger in KEYWORD_TRIGGERS and not split_keywords(rule.keywords):
		frappe.throw(_("Enter at least one keyword"))
	if rule.reply_type == "Buttons or List":
		__validate_options(rule)
	if rule.reply_type == "Action" and rule.action not in get_actions():
		frappe.throw(_("{0} is not an auto-reply action").format(rule.action))
	if rule.reply_type == "Template":
		status = frappe.db.get_value("WhatsApp Template", rule.template, "status")
		if status != "Approved":
			frappe.msgprint(_("Template {0} is not approved yet").format(rule.template), indicator="orange")


def split_keywords(text: str | None) -> list[str]:
	"""
	Return the keywords of a rule in lower case, one for each line.

	Parameters:
	        text (str, optional): The keywords field.

	Returns:
	        list[str]: The keywords without empty lines.
	"""
	return [line.strip().lower() for line in (text or "").splitlines() if line.strip()]


def __validate_options(rule) -> None:
	"""
	Check that there are 1 to 10 options with unique IDs; an empty ID is made from the title.

	Parameters:
	        rule (Document, required): The WhatsApp Auto Reply.

	Returns:
	        None
	"""
	if not 1 <= len(rule.options) <= MAX_OPTIONS:
		frappe.throw(_("Add 1 to {0} options").format(MAX_OPTIONS))
	for option in rule.options:
		option.option_id = (option.option_id or frappe.scrub(option.title)).strip()[:200]
	ids = [option.option_id for option in rule.options]
	if len(set(ids)) != len(ids):
		frappe.throw(_("Each option needs a different ID"))
