# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Assign WhatsApp Inbox conversations to agents."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_inbox.conversations import check_access, get_profile_name

AGENT_ROLES = ("System Manager", "WhatsApp Manager", "WhatsApp User")


def assign(phone_number: str, user: str | None = None) -> None:
	"""
	Assign a conversation to a user, or remove the assignment when user is empty.

	The user gets a notification when someone else assigns the conversation.

	Parameters:
	        phone_number (str, required): The customer's number.
	        user (str, optional): A user with a WhatsApp role.

	Returns:
	        None
	"""
	check_access("write")
	number = get_profile_name(phone_number)
	if user and not __is_agent(user):
		frappe.throw(_("{0} cannot use the WhatsApp Inbox").format(user))
	frappe.db.set_value("WhatsApp Profile", number, "assigned_to", user or None)
	if user and user != frappe.session.user:
		__notify_assignee(number, user)


def get_agents() -> list[dict]:
	"""
	Return the enabled users who can use the inbox, for the assign menu.

	Returns:
	        list[dict]: {"name", "full_name"} rows.
	"""
	check_access("read")
	users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", AGENT_ROLES], "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)
	return frappe.get_all(
		"User",
		filters={"name": ["in", users or [""]], "enabled": 1, "user_type": "System User"},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)


def __is_agent(user: str) -> bool:
	"""
	Tell if a user is enabled and has a role that can use the inbox.

	Parameters:
	        user (str, required): The user name.

	Returns:
	        bool: True for an enabled user with a WhatsApp role.
	"""
	if not frappe.db.get_value("User", user, "enabled"):
		return False
	return bool(set(frappe.get_roles(user)) & set(AGENT_ROLES))


def __notify_assignee(number: str, user: str) -> None:
	"""
	Send a desk notification to the user who got the conversation.

	Parameters:
	        number (str, required): The WhatsApp Profile name.
	        user (str, required): The new assignee.

	Returns:
	        None
	"""
	from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

	name = frappe.db.get_value("WhatsApp Profile", number, "profile_name") or number
	enqueue_create_notification(
		user,
		{
			"type": "Assignment",
			"document_type": "WhatsApp Profile",
			"document_name": number,
			"subject": _("{0} assigned you the WhatsApp conversation with {1}").format(
				frappe.utils.get_fullname(frappe.session.user), name
			),
			"from_user": frappe.session.user,
		},
	)
