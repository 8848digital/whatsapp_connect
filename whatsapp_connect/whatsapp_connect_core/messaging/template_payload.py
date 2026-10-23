# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Payload builder for template messages (registered in hooks.py)."""

import json

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_utils import (
	MEDIA_HEADERS,
)
from whatsapp_connect.whatsapp_connect_core.messaging.media import get_media_object
from whatsapp_connect.whatsapp_connect_core.messaging.template_params import get_template_params

BUTTON_SUB_TYPES = {
	"URL": "url",
	"One-Time Password": "url",
	"Copy Code": "copy_code",
	"Flow": "flow",
}


def build_template_object(message, api: CloudAPI) -> dict:
	"""
	Build the "template" object of a template message.

	Parameters:
	        message (Document, required): A WhatsApp Message with message_type "template".
	        api (CloudAPI, required): Client of the sending account (used for media headers).

	Returns:
	        dict: name, language and components.
	"""
	if not message.template:
		frappe.throw(_("Select the template to send"))
	template = frappe.get_cached_doc("WhatsApp Template", message.template)
	if template.status != "Approved":
		frappe.throw(
			_("Template {0} is not approved by Meta (status: {1})").format(
				template.name, _(template.status)
			)
		)

	params = __params(message, template)
	components = []
	header = __header(template, params, api)
	if header:
		components.append(header)
	if params["body"]:
		components.append(
			{"type": "body", "parameters": [{"type": "text", "text": value} for value in params["body"]]}
		)
	components.extend(__buttons(template, params))
	return {
		"name": template.template_name,
		"language": {"code": template.language_code},
		"components": components,
	}


def __params(message, template) -> dict:
	"""
	Use the values stored on the message, or read them from its reference document.

	Parameters:
	        message (Document, required): The WhatsApp Message.
	        template (Document, required): The WhatsApp Template.

	Returns:
	        dict: Complete template values; stored back on the message for reference.
	"""
	stored = (
		json.loads(message.template_params)
		if isinstance(message.template_params, str) and message.template_params
		else (message.template_params or {})
	)
	doc = None
	if (
		message.reference_doctype
		and message.reference_name
		and frappe.db.exists(message.reference_doctype, message.reference_name)
	):
		doc = frappe.get_doc(message.reference_doctype, message.reference_name)
	params = get_template_params(template, doc, stored)
	message.template_params = json.dumps(params)
	return params


def __header(template, params: dict, api: CloudAPI) -> dict | None:
	"""
	Build the header component: a text variable or a media file.

	Parameters:
	        template (Document, required): The WhatsApp Template.
	        params (dict, required): The template values.
	        api (CloudAPI, required): Client used to upload a local header file.

	Returns:
	        dict | None: The header component, or None when nothing has to be sent.
	"""
	if template.header_type == "Text" and params["header"]:
		return {"type": "header", "parameters": [{"type": "text", "text": params["header"][0]}]}
	if template.header_type in MEDIA_HEADERS:
		if not params.get("header_media"):
			frappe.throw(_("Template {0} needs a header file").format(template.name))
		kind = template.header_type.lower()
		media = get_media_object(api, params["header_media"], params.get("header_filename"), kind)
		return {"type": "header", "parameters": [{"type": kind, kind: media}]}
	return None


def __buttons(template, params: dict) -> list[dict]:
	"""
	Build the button components for buttons that take a value when sent.

	Parameters:
	        template (Document, required): The WhatsApp Template.
	        params (dict, required): The template values, with "buttons" by index.

	Returns:
	        list[dict]: Button components.
	"""
	components = []
	for index, button in enumerate(template.buttons):
		sub_type = BUTTON_SUB_TYPES.get(button.button_type)
		value = params["buttons"].get(str(index))
		if not sub_type or value in (None, ""):
			continue
		if sub_type == "copy_code":
			parameter = {"type": "coupon_code", "coupon_code": value}
		elif sub_type == "flow":
			parameter = {"type": "action", "action": {"flow_token": value}}
		else:
			parameter = {"type": "text", "text": value}
		components.append(
			{"type": "button", "sub_type": sub_type, "index": str(index), "parameters": [parameter]}
		)
	return components
