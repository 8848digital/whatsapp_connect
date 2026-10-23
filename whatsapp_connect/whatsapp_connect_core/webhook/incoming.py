# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""The "messages" webhook field: incoming messages and delivery statuses."""

import json

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_account.account_utils import (
	get_account_by_phone_number_id,
)
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_profile.profile_utils import (
	record_incoming,
)
from whatsapp_connect.whatsapp_connect_core.messaging.opt_out import apply_keyword
from whatsapp_connect.whatsapp_connect_core.webhook.common import to_datetime
from whatsapp_connect.whatsapp_connect_core.webhook.statuses import update_statuses

MEDIA_TYPES = ("image", "video", "audio", "document", "sticker")
KEYWORD_TYPES = ("text", "button")


def handle_messages_change(value: dict) -> None:
	"""
	Save the incoming messages and apply the delivery statuses of one change.

	Parameters:
	        value (dict, required): The change value: metadata, contacts, messages, statuses.

	Returns:
	        None
	"""
	update_statuses(value.get("statuses") or [])

	messages = value.get("messages") or []
	if not messages:
		return
	account = get_account_by_phone_number_id((value.get("metadata") or {}).get("phone_number_id"))
	if not account:
		return
	names = {
		contact.get("wa_id"): (contact.get("profile") or {}).get("name")
		for contact in value.get("contacts") or []
	}
	for message in messages:
		IncomingMessage(message, account, names.get(message.get("from"))).save()


class IncomingMessage:
	"""Turns one incoming message object from Meta into a WhatsApp Message."""

	def __init__(self, data: dict, account: str, profile_name: str | None):
		"""
		Keep the raw message and where it arrived.

		Parameters:
		        data (dict, required): Meta's message object.
		        account (str, required): The receiving WhatsApp Account.
		        profile_name (str, optional): The sender's WhatsApp name.

		Returns:
		        None
		"""
		self.data = data
		self.account = account
		self.profile_name = profile_name
		self.message_type = data.get("type") or "unsupported"

	def save(self) -> str | None:
		"""
		Insert the message, then do the follow-up work (media, opt-out, read receipt).

		Meta can deliver the same message twice; a known message ID is skipped.

		Returns:
		        str | None: The new WhatsApp Message name, or None for a duplicate.
		"""
		if frappe.db.exists("WhatsApp Message", {"wamid": self.data.get("id")}):
			return None

		received_at = to_datetime(self.data.get("timestamp"))
		record_incoming(self.data["from"], self.profile_name, self.account, received_at)
		message = frappe.get_doc(self.__document()).insert(ignore_permissions=True)

		if message.message_type in KEYWORD_TYPES:
			apply_keyword(message.phone_number, message.body, self.account)
		if message.media_id:
			frappe.enqueue(
				"whatsapp_connect.whatsapp_connect_core.messaging.media.save_incoming_media",
				message_name=message.name,
				enqueue_after_commit=True,
			)
		# Other modules act on incoming messages, for example Flow answers.
		for path in frappe.get_hooks("whatsapp_connect_incoming_handlers"):
			frappe.get_attr(path)(message)
		if frappe.db.get_value("WhatsApp Account", self.account, "send_read_receipts"):
			frappe.enqueue(
				"whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_message.message_utils.send_read_receipt",
				message_name=message.name,
				enqueue_after_commit=True,
			)
		return message.name

	def __document(self) -> dict:
		"""
		Build the WhatsApp Message fields for this message type.

		Returns:
		        dict: Document values for frappe.get_doc.
		"""
		values = {
			"doctype": "WhatsApp Message",
			"direction": "Incoming",
			"whatsapp_account": self.account,
			"phone_number": self.data["from"],
			"wamid": self.data.get("id"),
			"message_type": self.message_type,
			"source": "WhatsApp",
		}
		context = self.data.get("context") or {}
		if context.get("id") and not context.get("forwarded"):
			values["reply_to_wamid"] = context["id"]

		reader = getattr(self, f"_read_{self.message_type}", None)
		if self.message_type in MEDIA_TYPES:
			reader = self._read_media
		values.update(reader() if reader else self._read_unsupported())
		return values

	def _read_text(self) -> dict:
		"""
		Fields of a text message.

		Returns:
		        dict: {"body": text}
		"""
		return {"body": (self.data.get("text") or {}).get("body")}

	def _read_media(self) -> dict:
		"""
		Fields of an image, video, audio, document or sticker; the file is downloaded later.

		Returns:
		        dict: media_id, mime_type, caption as body, and filename.
		"""
		media = self.data.get(self.message_type) or {}
		return {
			"media_id": media.get("id"),
			"mime_type": media.get("mime_type"),
			"body": media.get("caption"),
			"filename": media.get("filename"),
		}

	def _read_reaction(self) -> dict:
		"""
		Fields of a reaction to an earlier message.

		Returns:
		        dict: reaction_emoji and reply_to_wamid.
		"""
		reaction = self.data.get("reaction") or {}
		return {"reaction_emoji": reaction.get("emoji"), "reply_to_wamid": reaction.get("message_id")}

	def _read_interactive(self) -> dict:
		"""
		Fields of a reply to buttons or a list, or of Flow answers (nfm_reply).

		Returns:
		        dict: body and payload; message_type "flow" for Flow answers.
		"""
		interactive = self.data.get("interactive") or {}
		if interactive.get("type") == "nfm_reply":
			reply = interactive.get("nfm_reply") or {}
			try:
				answers = json.loads(reply.get("response_json") or "{}")
			except ValueError:
				answers = {}
			return {
				"message_type": "flow",
				"body": reply.get("body") or _("Flow answers"),
				"payload": json.dumps(answers),
			}

		reply = interactive.get(interactive.get("type") or "") or {}
		return {"body": reply.get("title"), "payload": json.dumps(reply)}

	def _read_button(self) -> dict:
		"""
		Fields of a tap on a template quick-reply button.

		Returns:
		        dict: body (button text) and payload.
		"""
		button = self.data.get("button") or {}
		return {"body": button.get("text"), "payload": json.dumps(button)}

	def _read_order(self) -> dict:
		"""
		Fields of a catalog order.

		Returns:
		        dict: body and the order as payload.
		"""
		order = self.data.get("order") or {}
		return {"body": order.get("text") or _("Order received"), "payload": json.dumps(order)}

	def _read_location(self) -> dict:
		"""
		Fields of a shared location.

		Returns:
		        dict: body (name, address and coordinates) and payload.
		"""
		location = self.data.get("location") or {}
		parts = [
			location.get("name"),
			location.get("address"),
			f"{location.get('latitude')}, {location.get('longitude')}",
		]
		return {"body": " · ".join(part for part in parts if part), "payload": json.dumps(location)}

	def _read_contacts(self) -> dict:
		"""
		Fields of shared contact cards.

		Returns:
		        dict: body (contact names) and payload.
		"""
		contacts = self.data.get("contacts") or []
		names = [(contact.get("name") or {}).get("formatted_name") for contact in contacts]
		return {"body": ", ".join(name for name in names if name), "payload": json.dumps(contacts)}

	def _read_unsupported(self) -> dict:
		"""
		Fields of a message type the app does not handle: the raw data is kept.

		Returns:
		        dict: message_type "unsupported" and payload.
		"""
		return {"message_type": "unsupported", "payload": json.dumps(self.data)}
