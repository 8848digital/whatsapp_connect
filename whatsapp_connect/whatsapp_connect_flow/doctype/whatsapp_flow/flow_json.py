# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Validate a WhatsApp Flow and build its Flow JSON from the screens and components."""

import json
import re

import frappe
from frappe import _

FLOW_JSON_VERSION = "6.0"
DATA_API_VERSION = "3.0"
SCREEN_ID = re.compile(r"^[A-Z][A-Z0-9_]*$")
FIELD_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
TEXT_TYPES = ("TextHeading", "TextSubheading", "TextBody", "TextCaption")
CHOICE_TYPES = ("Dropdown", "RadioButtonsGroup", "CheckboxGroup")
MAX_CTA = 30


def validate_flow(flow) -> None:
	"""
	Check the screens and components, then write the generated Flow JSON.

	With Edit Flow JSON Directly, only the JSON itself is checked.

	Parameters:
	        flow (Document, required): The WhatsApp Flow being saved.

	Returns:
	        None
	"""
	if flow.cta and len(flow.cta) > MAX_CTA:
		frappe.throw(_("The button text can have at most {0} characters").format(MAX_CTA))
	if flow.edit_json:
		if not flow.flags.from_meta:
			__check_json(flow.flow_json)
		return
	if not flow.screens:
		return
	__validate_screens(flow)
	__validate_components(flow)
	flow.flow_json = json.dumps(build_flow_json(flow), indent=2)


def build_flow_json(flow) -> dict:
	"""
	Build the Flow JSON: one form per screen; each screen passes the earlier answers on.

	Parameters:
	        flow (Document, required): The WhatsApp Flow.

	Returns:
	        dict: The Flow JSON object.
	"""
	screens = []
	earlier = []  # (field_name, component) of the screens already built
	for index, screen in enumerate(flow.screens):
		is_last = index == len(flow.screens) - 1
		components = [row for row in flow.components if row.screen_id == screen.screen_id]
		fields = [row for row in components if row.component_type not in TEXT_TYPES]
		children = [component_json(row) for row in components]
		children.append(__footer(screen, flow, earlier, fields, is_last))
		screen_json = {
			"id": screen.screen_id,
			"title": screen.title,
			"data": {row.field_name: data_type(row) for row in earlier},
			"layout": {
				"type": "SingleColumnLayout",
				"children": [{"type": "Form", "name": "form", "children": children}],
			},
		}
		if is_last:
			screen_json["terminal"] = True
			screen_json["success"] = True
		screens.append(screen_json)
		earlier += fields

	flow_json = {"version": FLOW_JSON_VERSION, "screens": screens}
	if flow.use_endpoint:
		flow_json["data_api_version"] = DATA_API_VERSION
	return flow_json


def component_json(row) -> dict:
	"""
	Build one component of a form.

	Parameters:
	        row (Document, required): A WhatsApp Flow Component row.

	Returns:
	        dict: The component in Flow JSON.
	"""
	if row.component_type in TEXT_TYPES:
		return {"type": row.component_type, "text": row.label}
	component = {"type": row.component_type, "name": row.field_name, "label": row.label}
	if row.component_type != "OptIn":
		component["required"] = bool(row.required)
	if row.component_type == "TextInput":
		component["input-type"] = row.input_type or "text"
	if row.component_type in CHOICE_TYPES:
		component["data-source"] = parse_choices(row.choices)
	if row.helper_text and row.component_type in ("TextInput", "TextArea", "DatePicker"):
		component["helper-text"] = row.helper_text
	if row.component_type == "OptIn" and row.required:
		component["required"] = True
	return component


def data_type(row) -> dict:
	"""
	Declare an earlier answer in a screen's "data", with an example value.

	Parameters:
	        row (Document, required): A WhatsApp Flow Component row with an answer.

	Returns:
	        dict: The data declaration.
	"""
	if row.component_type == "CheckboxGroup":
		return {"type": "array", "items": {"type": "string"}, "__example__": []}
	if row.component_type == "OptIn":
		return {"type": "boolean", "__example__": False}
	return {"type": "string", "__example__": ""}


def parse_choices(value: str | None) -> list[dict]:
	"""
	Read "id|Title" or "Title" lines into Flow data-source items.

	Parameters:
	        value (str, optional): One choice per line.

	Returns:
	        list[dict]: [{"id": ..., "title": ...}]
	"""
	choices = []
	for line in (value or "").splitlines():
		if not line.strip():
			continue
		choice_id, _sep, title = (
			line.partition("|") if "|" in line else (frappe.scrub(line.strip()), "", line)
		)
		choices.append({"id": choice_id.strip(), "title": title.strip()})
	return choices


def __footer(screen, flow, earlier: list, fields: list, is_last: bool) -> dict:
	"""
	Build the screen's footer button: go to the next screen, or complete the flow.

	Parameters:
	        screen (Document, required): The WhatsApp Flow Screen.
	        flow (Document, required): The WhatsApp Flow.
	        earlier (list, required): Answer components of the earlier screens.
	        fields (list, required): Answer components of this screen.
	        is_last (bool, required): True for the last screen.

	Returns:
	        dict: The Footer component.
	"""
	payload = {row.field_name: f"${{data.{row.field_name}}}" for row in earlier}
	payload.update({row.field_name: f"${{form.{row.field_name}}}" for row in fields})
	label = screen.footer_label or (_("Submit") if is_last else _("Continue"))
	if is_last:
		action = {"name": "complete", "payload": payload}
	elif flow.use_endpoint:
		action = {"name": "data_exchange", "payload": payload}
	else:
		next_screen = flow.screens[flow.screens.index(screen) + 1].screen_id
		action = {
			"name": "navigate",
			"next": {"type": "screen", "name": next_screen},
			"payload": payload,
		}
	return {"type": "Footer", "label": label, "on-click-action": action}


def __validate_screens(flow) -> None:
	"""
	Check the screen IDs.

	Parameters:
	        flow (Document, required): The WhatsApp Flow.

	Returns:
	        None
	"""
	ids = [screen.screen_id for screen in flow.screens]
	for screen in flow.screens:
		if not SCREEN_ID.match(screen.screen_id or ""):
			frappe.throw(
				_("Screen {0}: use capital letters, digits and underscores").format(screen.screen_id)
			)
	if len(ids) != len(set(ids)):
		frappe.throw(_("Each screen needs its own Screen ID"))


def __validate_components(flow) -> None:
	"""
	Check that components use known screens, valid unique field names, and have choices.

	Parameters:
	        flow (Document, required): The WhatsApp Flow.

	Returns:
	        None
	"""
	screen_ids = {screen.screen_id for screen in flow.screens}
	names = []
	for row in flow.components:
		if row.screen_id not in screen_ids:
			frappe.throw(_("Component row {0}: there is no screen {1}").format(row.idx, row.screen_id))
		if row.component_type in TEXT_TYPES:
			continue
		if not FIELD_NAME.match(row.field_name or ""):
			frappe.throw(
				_(
					"Component row {0}: the field name must start with a lowercase letter and use only lowercase letters, digits and underscores"
				).format(row.idx)
			)
		if row.component_type in CHOICE_TYPES and not parse_choices(row.choices):
			frappe.throw(_("Component row {0}: add the choices").format(row.idx))
		names.append(row.field_name)
	if len(names) != len(set(names)):
		frappe.throw(_("Each answer needs its own field name"))


def __check_json(value: str | None) -> None:
	"""
	Check that hand-written Flow JSON is valid JSON with screens.

	Parameters:
	        value (str, optional): The Flow JSON.

	Returns:
	        None
	"""
	try:
		data = json.loads(value or "")
	except ValueError:
		frappe.throw(_("The Flow JSON is not valid JSON"))
	if not isinstance(data, dict) or not data.get("screens"):
		frappe.throw(_("The Flow JSON needs a version and screens"))
