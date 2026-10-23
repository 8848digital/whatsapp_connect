# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Validation of WhatsApp Templates and the component list that Meta expects."""

import re

import frappe
from frappe import _

NAME_PATTERN = re.compile(r"^[a-z0-9_]{1,512}$")
VARIABLE_PATTERN = re.compile(r"\{\{(\d+)\}\}")
MEDIA_HEADERS = ("Image", "Document", "Video")
MAX_BUTTON_LABEL = 25
MAX_FOOTER = 60
META_BUTTON_TYPES = {
	"Quick Reply": "QUICK_REPLY",
	"Phone Number": "PHONE_NUMBER",
	"URL": "URL",
	"Copy Code": "COPY_CODE",
	"One-Time Password": "OTP",
	"Flow": "FLOW",
	"Catalog": "CATALOG",
	"Multi-Product": "MPM",
}


def validate_template(template) -> None:
	"""
	Check the name, variables, samples, footer and buttons before saving.

	Parameters:
	        template (Document, required): The WhatsApp Template being saved.

	Returns:
	        None
	"""
	template.template_name = (template.template_name or "").strip().lower().replace(" ", "_")
	if not NAME_PATTERN.match(template.template_name):
		frappe.throw(_("The template name may contain only lowercase letters, digits and underscores"))
	if template.footer and len(template.footer) > MAX_FOOTER:
		frappe.throw(_("The footer can have at most {0} characters").format(MAX_FOOTER))

	count = variable_count(template.body)
	samples = split_lines(template.body_samples)
	if (
		template.category != "AUTHENTICATION"
		and count
		and len(samples) < count
		and not template.flags.from_meta
	):
		frappe.throw(
			_("Add a sample for each variable: the text has {0}, the samples have {1}").format(
				count, len(samples)
			)
		)

	for button in template.buttons:
		__validate_button(button)


def variable_count(text: str | None) -> int:
	"""
	Count the variables {{1}}..{{n}} and check that they are numbered without gaps.

	Parameters:
	        text (str, optional): Template text.

	Returns:
	        int: The highest variable number, 0 when there is none.
	"""
	numbers = sorted({int(number) for number in VARIABLE_PATTERN.findall(text or "")})
	if numbers and numbers != list(range(1, numbers[-1] + 1)):
		frappe.throw(_("Number the variables {{1}}, {{2}}... without gaps"))
	return numbers[-1] if numbers else 0


def split_lines(value: str | None) -> list[str]:
	"""
	Split a one-value-per-line field into its non-empty values.

	Parameters:
	        value (str, optional): The field value.

	Returns:
	        list[str]: The values, stripped.
	"""
	return [line.strip() for line in (value or "").splitlines() if line.strip()]


def build_components(template, header_handle: str | None = None) -> list[dict]:
	"""
	Build the "components" list that Meta expects when a template is created or edited.

	Parameters:
	        template (Document, required): The WhatsApp Template.
	        header_handle (str, optional): Handle of the uploaded sample file for a media header.

	Returns:
	        list[dict]: Header, body, footer and buttons components.
	"""
	if template.category == "AUTHENTICATION":
		return __authentication_components(template)

	components = []
	header = __header_component(template, header_handle)
	if header:
		components.append(header)

	body = {"type": "BODY", "text": template.body}
	samples = split_lines(template.body_samples)
	if variable_count(template.body):
		body["example"] = {"body_text": [samples[: variable_count(template.body)]]}
	components.append(body)

	if template.footer:
		components.append({"type": "FOOTER", "text": template.footer})
	if template.buttons:
		components.append(
			{"type": "BUTTONS", "buttons": [__button_component(button) for button in template.buttons]}
		)
	return components


def __header_component(template, header_handle: str | None) -> dict | None:
	"""
	Build the header component, or None when the template has no header.

	Parameters:
	        template (Document, required): The WhatsApp Template.
	        header_handle (str, optional): Handle of the uploaded sample file.

	Returns:
	        dict | None: The HEADER component.
	"""
	if template.header_type == "Text":
		header = {"type": "HEADER", "format": "TEXT", "text": template.header_text}
		if variable_count(template.header_text):
			header["example"] = {"header_text": [template.header_sample or ""]}
		return header
	if template.header_type in MEDIA_HEADERS:
		header = {"type": "HEADER", "format": template.header_type.upper()}
		if header_handle:
			header["example"] = {"header_handle": [header_handle]}
		return header
	return None


def __button_component(button) -> dict:
	"""
	Build one button of the BUTTONS component.

	Parameters:
	        button (Document, required): A WhatsApp Template Button row.

	Returns:
	        dict: The button in Meta's format.
	"""
	meta_type = META_BUTTON_TYPES[button.button_type]
	component = {"type": meta_type, "text": button.label}
	if meta_type == "PHONE_NUMBER":
		component["phone_number"] = button.phone_number
	elif meta_type == "URL":
		component["url"] = button.url
		if variable_count(button.url):
			component["example"] = [button.url_sample or button.url]
	elif meta_type == "COPY_CODE":
		component = {"type": "COPY_CODE", "example": button.code_sample or "CODE123"}
	elif meta_type == "OTP":
		component = {"type": "OTP", "otp_type": "COPY_CODE", "text": button.label or "Copy code"}
	elif meta_type == "FLOW":
		component.update(
			{"flow_id": button.flow_id, "flow_action": "navigate", "navigate_screen": button.flow_screen}
		)
	return component


def __authentication_components(template) -> list[dict]:
	"""
	Build the fixed components of an authentication (one-time password) template.

	Meta writes the body text itself for this category.

	Parameters:
	        template (Document, required): An AUTHENTICATION WhatsApp Template.

	Returns:
	        list[dict]: Body with the security notice and a copy-code button.
	"""
	label = next(
		(button.label for button in template.buttons if button.button_type == "One-Time Password"), None
	)
	return [
		{"type": "BODY", "add_security_recommendation": True},
		{
			"type": "BUTTONS",
			"buttons": [{"type": "OTP", "otp_type": "COPY_CODE", "text": label or "Copy code"}],
		},
	]


def __validate_button(button) -> None:
	"""
	Check the fields that each button type needs.

	Parameters:
	        button (Document, required): A WhatsApp Template Button row.

	Returns:
	        None
	"""
	if button.button_type not in ("Copy Code",) and not button.label:
		frappe.throw(_("Row {0}: enter the button label").format(button.idx))
	if button.label and len(button.label) > MAX_BUTTON_LABEL:
		frappe.throw(
			_("Row {0}: a button label can have at most {1} characters").format(
				button.idx, MAX_BUTTON_LABEL
			)
		)
	if button.button_type == "Phone Number" and not button.phone_number:
		frappe.throw(_("Row {0}: enter the phone number").format(button.idx))
	if button.button_type == "URL" and not button.url:
		frappe.throw(_("Row {0}: enter the URL").format(button.idx))
	if button.button_type == "Flow" and not button.flow_id:
		frappe.throw(_("Row {0}: enter the Flow ID").format(button.idx))
