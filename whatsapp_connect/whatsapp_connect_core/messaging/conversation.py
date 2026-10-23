# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Conversation state on the WhatsApp Profile, and realtime events for the WhatsApp Inbox."""

import frappe
from frappe import _
from frappe.query_builder.functions import Coalesce
from frappe.utils import now_datetime, strip_html_tags

# Sent to the "doctype:WhatsApp Message" room, so only users who can read messages get it.
REALTIME_EVENT = "whatsapp_connect_message"
PREVIEW_LENGTH = 140
TYPE_LABELS = {
	"image": "Photo",
	"video": "Video",
	"audio": "Audio",
	"document": "Document",
	"sticker": "Sticker",
	"location": "Location",
	"contacts": "Contact",
	"order": "Order",
	"flow": "Flow answers",
}


def record_message(message) -> None:
	"""
	Update the conversation of the message's profile and tell open inboxes.

	An incoming message counts as unread and opens a closed conversation again.
	Reactions change neither the preview nor the counters.

	Parameters:
	        message (Document, required): An inserted WhatsApp Message.

	Returns:
	        None
	"""
	if message.message_type != "reaction" and message.profile:
		__update_profile(message)
	publish(message.name, message.phone_number, "new")


def publish(message_name: str, phone_number: str | None, event: str) -> None:
	"""
	Tell the open WhatsApp Inboxes that a message is new or has a new status.

	Parameters:
	        message_name (str, required): The WhatsApp Message name.
	        phone_number (str, optional): The customer's number (the conversation).
	        event (str, required): "new" or "status".

	Returns:
	        None
	"""
	frappe.publish_realtime(
		REALTIME_EVENT,
		{"message": message_name, "phone_number": phone_number, "event": event},
		doctype="WhatsApp Message",
		after_commit=True,
	)


def message_preview(message) -> str:
	"""
	Return the short text shown for a message in the conversation list.

	Parameters:
	        message (Document | dict, required): A WhatsApp Message.

	Returns:
	        str: The text, the template name or the type of the message.
	"""
	text = strip_html_tags(message.get("body") or "").strip()
	if not text and message.get("template"):
		text = _("Template: {0}").format(message.get("template"))
	if not text:
		text = _(TYPE_LABELS.get(message.get("message_type"), message.get("message_type") or ""))
	if len(text) > PREVIEW_LENGTH:
		text = text[: PREVIEW_LENGTH - 1] + "…"
	return text


def __update_profile(message) -> None:
	"""
	Save the last message on the profile; for incoming messages, count it as unread.

	The counter is increased in SQL, so two messages that arrive together both count.

	Parameters:
	        message (Document, required): The WhatsApp Message.

	Returns:
	        None
	"""
	profile = frappe.qb.DocType("WhatsApp Profile")
	query = (
		frappe.qb.update(profile)
		.set(profile.last_message_at, message.creation or now_datetime())
		.set(profile.last_message_preview, message_preview(message))
		.set(profile.last_message_direction, message.direction)
		.where(profile.name == message.profile)
	)
	if message.direction == "Incoming":
		query = query.set(profile.unread_count, Coalesce(profile.unread_count, 0) + 1)
		status = frappe.db.get_value("WhatsApp Profile", message.profile, "conversation_status")
		if status in (None, "", "Closed"):
			query = query.set(profile.conversation_status, "Open")
	query.run()
