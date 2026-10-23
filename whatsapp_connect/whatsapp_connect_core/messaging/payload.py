# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Build the Cloud API message object from a WhatsApp Message.

Other modules add builders for their message types through the
"whatsapp_connect_payload_builders" hook, for example
{"template": "whatsapp_connect...build_template_object"}.
"""

import json

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI
from whatsapp_connect.whatsapp_connect_core.messaging.media import get_media_object

MEDIA_TYPES = ("image", "document", "video", "audio", "sticker")
CAPTION_TYPES = ("image", "document", "video")
MAX_BUTTONS = 3
MAX_LIST_ROWS = 10
MAX_BUTTON_TITLE = 20


def build_payload(message, api: CloudAPI) -> dict:
	"""
	Return the message object to send, without "messaging_product".

	Parameters:
	        message (Document, required): An outgoing WhatsApp Message.
	        api (CloudAPI, required): Client of the sending account (used for media uploads).

	Returns:
	        dict: The Cloud API message object.
	"""
	payload = {
		"recipient_type": "individual",
		"to": message.phone_number,
		"type": message.message_type,
	}
	if message.reply_to_wamid and message.message_type != "reaction":
		payload["context"] = {"message_id": message.reply_to_wamid}

	builder = __get_builder(message.message_type)
	payload[message.message_type] = builder(message, api)
	return payload


def build_text(message, api: CloudAPI) -> dict:
	"""
	Text object. Links in the text get a preview.

	Parameters:
	        message (Document, required): The WhatsApp Message.
	        api (CloudAPI, required): Unused; part of the builder signature.

	Returns:
	        dict: {"body": ..., "preview_url": True}
	"""
	if not (message.body or "").strip():
		frappe.throw(_("Enter the message text"))
	return {"body": message.body, "preview_url": True}


def build_media(message, api: CloudAPI) -> dict:
	"""
	Image, document, video, audio or sticker object; the file is uploaded to Meta when stored here.

	Parameters:
	        message (Document, required): The WhatsApp Message with an attachment.
	        api (CloudAPI, required): Client used to upload the file.

	Returns:
	        dict: Media object with "id" or "link", and "caption" where WhatsApp allows one.
	"""
	if not message.attachment:
		frappe.throw(_("Attach a file to send a {0} message").format(_(message.message_type)))
	media = get_media_object(api, message.attachment, message.filename, message.message_type)
	if media.get("id"):
		message.media_id = media["id"]
	if message.message_type in CAPTION_TYPES and message.body:
		media["caption"] = message.body
	return media


def build_reaction(message, api: CloudAPI) -> dict:
	"""
	Reaction object: an emoji on an earlier message.

	Parameters:
	        message (Document, required): The WhatsApp Message with reply_to_wamid and reaction_emoji.
	        api (CloudAPI, required): Unused; part of the builder signature.

	Returns:
	        dict: {"message_id": ..., "emoji": ...}
	"""
	if not message.reply_to_wamid:
		frappe.throw(_("Set the message to react to"))
	return {"message_id": message.reply_to_wamid, "emoji": message.reaction_emoji or ""}


def build_interactive(message, api: CloudAPI) -> dict:
	"""
	Interactive object: reply buttons (up to 3) or a list (up to 10 rows).

	Parameters:
	        message (Document, required): The WhatsApp Message with body and interactive_options.
	        api (CloudAPI, required): Unused; part of the builder signature.

	Returns:
	        dict: The "button" or "list" interactive object.
	"""
	options = __parse_options(message.interactive_options)
	body = {"text": message.body or ""}
	if len(options) <= MAX_BUTTONS:
		buttons = [
			{"type": "reply", "reply": {"id": option["id"], "title": option["title"][:MAX_BUTTON_TITLE]}}
			for option in options
		]
		return {"type": "button", "body": body, "action": {"buttons": buttons}}

	if len(options) > MAX_LIST_ROWS:
		frappe.throw(_("A list can have at most {0} options").format(MAX_LIST_ROWS))
	rows = [
		{
			"id": option["id"],
			"title": option["title"][:24],
			"description": option.get("description", "")[:72],
		}
		for option in options
	]
	button_label = (message.list_button_label or _("Options"))[:MAX_BUTTON_TITLE]
	return {
		"type": "list",
		"body": body,
		"action": {"button": button_label, "sections": [{"title": button_label, "rows": rows}]},
	}


BUILDERS = {
	"text": build_text,
	"reaction": build_reaction,
	"interactive": build_interactive,
	**{media_type: build_media for media_type in MEDIA_TYPES},
}


def __get_builder(message_type: str):
	"""
	Find the builder for a message type: built-in, or registered by another module.

	Parameters:
	        message_type (str, required): The WhatsApp Message type.

	Returns:
	        callable: A function (message, api) -> dict.
	"""
	hooked = frappe.get_hooks("whatsapp_connect_payload_builders", default={}).get(message_type)
	if hooked:
		return frappe.get_attr(hooked[-1])
	if message_type in BUILDERS:
		return BUILDERS[message_type]
	frappe.throw(_("Messages of type {0} cannot be sent").format(message_type))


def __parse_options(value) -> list[dict]:
	"""
	Read and check the interactive options.

	Parameters:
	        value (str | list, optional): JSON list of {"id", "title"} objects.

	Returns:
	        list[dict]: The options.
	"""
	options = json.loads(value) if isinstance(value, str) else (value or [])
	if not options or not all(
		isinstance(o, dict) and o.get("id") and o.get("title") for o in options
	):
		frappe.throw(_("Add options with an id and a title"))
	return options
