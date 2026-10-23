# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Fill the new conversation fields of WhatsApp Profiles from their latest message."""

import frappe

from whatsapp_connect.whatsapp_connect_core.messaging.conversation import message_preview


def execute() -> None:
	"""
	Set the last message of each profile, and mark numbers that wrote as Open conversations.

	Returns:
	        None
	"""
	for profile in frappe.get_all("WhatsApp Profile", fields=["name", "last_incoming_at"]):
		latest = frappe.get_all(
			"WhatsApp Message",
			filters={"phone_number": profile.name, "message_type": ["!=", "reaction"]},
			fields=["body", "template", "message_type", "direction", "creation"],
			order_by="creation desc",
			limit=1,
		)
		if not latest:
			continue
		values = {
			"last_message_at": latest[0].creation,
			"last_message_preview": message_preview(latest[0]),
			"last_message_direction": latest[0].direction,
		}
		if profile.last_incoming_at:
			values["conversation_status"] = "Open"
		frappe.db.set_value("WhatsApp Profile", profile.name, values, update_modified=False)
