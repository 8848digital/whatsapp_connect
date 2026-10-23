# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Messages of a conversation as the WhatsApp Inbox shows them."""

import json

import frappe

MESSAGE_FIELDS = [
	"name",
	"phone_number",
	"direction",
	"message_type",
	"status",
	"body",
	"attachment",
	"filename",
	"mime_type",
	"template",
	"template_params",
	"reaction_emoji",
	"reply_to_wamid",
	"wamid",
	"interactive_options",
	"error_message",
	"source",
	"owner",
	"creation",
]


def get_message_rows(number: str, before: str | None, limit: int) -> list[dict]:
	"""
	Return the latest messages of a number, oldest first, with template text filled in.

	Parameters:
	        number (str, required): The WhatsApp Profile name.
	        before (str, optional): Only messages created before this time.
	        limit (int, required): Messages to return.

	Returns:
	        list[dict]: Message rows; templates get "template_text", "template_header" and "template_footer".
	"""
	filters = {"phone_number": number}
	if before:
		filters["creation"] = ["<", before]
	rows = frappe.get_all(
		"WhatsApp Message",
		filters=filters,
		fields=MESSAGE_FIELDS,
		order_by="creation desc",
		limit=limit,
	)
	templates = {}
	for row in rows:
		if row.message_type == "template" and row.template:
			row.update(__template_text(row, templates))
		row.pop("template_params", None)
	rows.reverse()
	return rows


def get_reference(number: str) -> dict | None:
	"""
	Return the record the conversation belongs to: the latest linked message's document.

	Parameters:
	        number (str, required): The WhatsApp Profile name.

	Returns:
	        dict | None: {"doctype", "name"}, or None when no message is linked.
	"""
	row = frappe.get_all(
		"WhatsApp Message",
		filters={"phone_number": number, "reference_name": ["is", "set"]},
		fields=["reference_doctype", "reference_name"],
		order_by="creation desc",
		limit=1,
	)
	if not row:
		return None
	return {"doctype": row[0].reference_doctype, "name": row[0].reference_name}


def __template_text(row: dict, templates: dict) -> dict:
	"""
	Fill a sent template's text with the values it was sent with.

	Parameters:
	        row (dict, required): A template message row with template_params.
	        templates (dict, required): Cache of loaded templates by name.

	Returns:
	        dict: template_text, template_header and template_footer.
	"""
	if row.template not in templates:
		templates[row.template] = frappe.db.get_value(
			"WhatsApp Template",
			row.template,
			["body", "header_type", "header_text", "footer"],
			as_dict=True,
		)
	template = templates[row.template]
	if not template:
		return {}

	params = __load_params(row.template_params)
	body = template.body or ""
	for index, value in enumerate(params.get("body") or [], start=1):
		body = body.replace("{{%d}}" % index, str(value))
	header = (template.header_text or "") if template.header_type == "Text" else ""
	for value in (params.get("header") or [])[:1]:
		header = header.replace("{{1}}", str(value))
	return {"template_text": body, "template_header": header, "template_footer": template.footer}


def __load_params(value) -> dict:
	"""
	Read the stored template values.

	Parameters:
	        value (str | dict, optional): The template_params JSON.

	Returns:
	        dict: The values, or an empty dict when they cannot be read.
	"""
	if isinstance(value, dict):
		return value
	try:
		return json.loads(value or "{}") or {}
	except ValueError:
		return {}
