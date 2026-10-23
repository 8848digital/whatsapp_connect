# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Values for a template's variables: given by the caller, or read from a document."""

import re

import frappe
from frappe.utils import strip_html_tags

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_utils import (
	split_lines,
	variable_count,
)

DYNAMIC_BUTTONS = ("URL", "Copy Code", "One-Time Password", "Flow")
MAX_PARAM_LENGTH = 1024


def get_template_params(template, doc=None, values: dict | None = None) -> dict:
	"""
	Collect the header, body and button values for sending a template.

	Values given by the caller win; missing ones come from the document fields
	mapped on the template, and finally from the template's samples.

	Parameters:
	        template (Document, required): The WhatsApp Template.
	        doc (Document, optional): The document the message is about.
	        values (dict, optional): {"header": [...], "header_media": url, "body": [...], "buttons": {"0": value}}.

	Returns:
	        dict: The same structure, complete.
	"""
	values = values or {}
	params = {
		"header": values.get("header") or __header_values(template, doc),
		"header_media": values.get("header_media") or template.header_sample_file,
		"header_filename": values.get("header_filename"),
		"body": values.get("body") or __body_values(template, doc),
		"buttons": {str(key): value for key, value in (values.get("buttons") or {}).items()},
	}
	for index, button in enumerate(template.buttons):
		if button.button_type in DYNAMIC_BUTTONS and str(index) not in params["buttons"]:
			params["buttons"][str(index)] = __button_value(button, doc, params["body"])
	params["header"] = [clean_param(value) for value in params["header"]]
	params["body"] = [clean_param(value) for value in params["body"]]
	return params


def clean_param(value) -> str:
	"""
	Make a value acceptable to Meta as a template variable.

	Meta refuses variables with line breaks, tabs or more than four spaces in a
	row (error 132018), and cuts them at 1024 characters. HTML from text
	editor fields is removed too.

	Parameters:
	        value (Any, required): The raw value.

	Returns:
	        str: The cleaned text.
	"""
	text = strip_html_tags(str(value if value is not None else ""))
	text = re.sub(r"\s+", " ", text).strip()
	return text[:MAX_PARAM_LENGTH]


def __body_values(template, doc) -> list[str]:
	"""
	Read the body variables from the document's mapped fields, or use the samples.

	Parameters:
	        template (Document, required): The WhatsApp Template.
	        doc (Document, optional): The document.

	Returns:
	        list[str]: One value per variable.
	"""
	count = variable_count(template.body) or (1 if template.category == "AUTHENTICATION" else 0)
	fields = split_lines(template.body_fields)
	samples = split_lines(template.body_samples)
	result = []
	for index in range(count):
		field = fields[index] if index < len(fields) else None
		value = field_value(doc, field) if field else None
		result.append(
			value if value not in (None, "") else (samples[index] if index < len(samples) else "")
		)
	return result


def __header_values(template, doc) -> list[str]:
	"""
	Read the header variable of a text header.

	Parameters:
	        template (Document, required): The WhatsApp Template.
	        doc (Document, optional): The document.

	Returns:
	        list[str]: The header value, or an empty list when the header has no variable.
	"""
	if template.header_type != "Text" or not variable_count(template.header_text):
		return []
	value = field_value(doc, template.header_field) if template.header_field else None
	return [value if value not in (None, "") else (template.header_sample or "")]


def __button_value(button, doc, body: list[str]) -> str:
	"""
	Value of a dynamic button: the mapped field, a Flow token, or the code for OTP buttons.

	Parameters:
	        button (Document, required): A WhatsApp Template Button row.
	        doc (Document, optional): The document.
	        body (list[str], required): The body values (an OTP button repeats the code).

	Returns:
	        str: The button value.
	"""
	value = field_value(doc, button.value_field) if button.value_field else None
	if value not in (None, ""):
		return value
	if button.button_type == "Flow":
		return frappe.generate_hash(length=16)
	if button.button_type == "One-Time Password" and body:
		return body[0]
	return button.code_sample or ""


def field_value(doc, fieldname: str | None) -> str | None:
	"""
	Read a document field as display text (currency and dates formatted).

	Parameters:
	        doc (Document, optional): The document.
	        fieldname (str, optional): The field name.

	Returns:
	        str | None: The formatted value.
	"""
	if doc is None or not fieldname:
		return None
	if hasattr(doc, "get_formatted") and doc.meta.has_field(fieldname):
		return str(doc.get_formatted(fieldname) or "")
	value = doc.get(fieldname)
	return None if value is None else str(value)
