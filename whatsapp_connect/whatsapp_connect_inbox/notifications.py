# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Tell agents about new messages: a desk notification, a popup, and a browser notification."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.messaging.conversation import message_preview

# Sent to each agent; public/js/inbox_notifications.js shows the popup.
POPUP_EVENT = "whatsapp_connect_new_message"
NOTIFY_ROLES = ("WhatsApp Manager", "WhatsApp User")
NOTIFY_ASSIGNEE_OR_ALL = "Assigned user, else all agents"
NOTIFY_ASSIGNEE = "Assigned user only"


def handle_incoming(message) -> None:
	"""
	Notify the agents of a new incoming message (whatsapp_connect_incoming_handlers hook).

	Every message shows a popup. The first unread message of a conversation also
	adds a desk notification, so a customer who sends five lines adds one, not five.

	Parameters:
	        message (Document, required): The saved incoming WhatsApp Message.

	Returns:
	        None
	"""
	if message.message_type == "reaction":
		return
	profile = frappe.db.get_value(
		"WhatsApp Profile",
		message.profile,
		["name", "profile_name", "assigned_to", "unread_count"],
		as_dict=True,
	)
	users = get_recipients(profile.assigned_to) if profile else []
	if not users:
		return

	title = _("WhatsApp from {0}").format(profile.profile_name or f"+{profile.name}")
	text = message_preview(message)
	for user in users:
		frappe.publish_realtime(
			POPUP_EVENT,
			{"phone_number": profile.name, "title": title, "body": text},
			user=user,
			after_commit=True,
		)
	if profile.unread_count == 1:
		create_desk_notification(users, profile.name, title, text)


def get_recipients(assigned_to: str | None) -> list[str]:
	"""
	Return the users to notify, by the Inbox Notifications setting of WhatsApp Settings.

	Parameters:
	        assigned_to (str, optional): The conversation's assignee.

	Returns:
	        list[str]: User names; empty when notifications are off.
	"""
	setting = get_setting()
	if assigned_to and setting in (NOTIFY_ASSIGNEE_OR_ALL, NOTIFY_ASSIGNEE):
		return [assigned_to]
	if setting != NOTIFY_ASSIGNEE_OR_ALL:
		return []
	users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", NOTIFY_ROLES], "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)
	return frappe.get_all(
		"User",
		filters={"name": ["in", users or [""]], "enabled": 1, "user_type": "System User"},
		pluck="name",
	)


def get_setting() -> str:
	"""
	Return the Notify Agents of New Messages value of WhatsApp Settings.

	Returns:
	        str: One of the NOTIFY_* values or "Nobody".
	"""
	return (
		frappe.db.get_single_value("WhatsApp Settings", "inbox_notifications") or NOTIFY_ASSIGNEE_OR_ALL
	)


def create_desk_notification(
	users: list[str], number: str, subject: str, text: str | None = None
) -> None:
	"""
	Add a notification in the desk (bell icon) that opens the conversation in the inbox.

	Frappe 15 and later open the "link". Frappe 14 has no link field, so it opens
	the WhatsApp Profile, whose form has an Open in Inbox button.

	Parameters:
	        users (list[str], required): Users to notify.
	        number (str, required): The WhatsApp Profile name.
	        subject (str, required): The notification text.
	        text (str, optional): The message preview.

	Returns:
	        None
	"""
	from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

	enqueue_create_notification(
		users,
		{
			"type": "Alert",
			"document_type": "WhatsApp Profile",
			"document_name": number,
			"subject": subject,
			"email_content": frappe.utils.escape_html(text or ""),
			"link": inbox_link(number),
		},
	)


def inbox_link(number: str) -> str:
	"""
	Return the desk path that opens a conversation in the WhatsApp Inbox.

	Parameters:
	        number (str, required): The customer's number.

	Returns:
	        str: For example "/app/whatsapp-inbox/919900000101".
	"""
	return f"/app/whatsapp-inbox/{number}"
