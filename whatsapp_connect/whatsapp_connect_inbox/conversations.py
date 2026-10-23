# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Conversations of the WhatsApp Inbox: one for each customer number that wrote."""

import re

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, get_datetime, now_datetime

from whatsapp_connect.whatsapp_connect_core.messaging.reply_window import WINDOW_HOURS
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number
from whatsapp_connect.whatsapp_connect_inbox.message_view import get_message_rows, get_reference

STATUSES = ("Open", "Pending", "Closed")
MAX_PAGE_LENGTH = 100
CONVERSATION_FIELDS = [
	"name",
	"profile_name",
	"contact",
	"whatsapp_account",
	"conversation_status",
	"assigned_to",
	"unread_count",
	"last_message_at",
	"last_message_preview",
	"last_message_direction",
	"last_incoming_at",
	"opted_out",
]


def list_conversations(
	status: str | None = None,
	assigned_to: str | None = None,
	account: str | None = None,
	search: str | None = None,
	start: int = 0,
	page_length: int = 50,
) -> dict:
	"""
	Return the conversations for the inbox list, newest first, with the count of each tab.

	A number becomes a conversation when the customer writes or an agent sends a
	template from the inbox. Numbers that only got notifications or campaigns are left out.

	Parameters:
	        status (str, optional): "Open", "Pending" or "Closed"; all when empty.
	        assigned_to (str, optional): A user, "me" or "unassigned"; everyone when empty.
	        account (str, optional): Only this WhatsApp Account.
	        search (str, optional): Part of the number or the WhatsApp name.
	        start (int, optional): Rows to skip.
	        page_length (int, optional): Rows to return, at most 100.

	Returns:
	        dict: {"conversations": [...], "counts": {"Open": 3, ...}}
	"""
	check_access("read")
	filters = __filters(assigned_to, account, search)
	rows = frappe.get_all(
		"WhatsApp Profile",
		filters={**filters, **({"conversation_status": status} if status in STATUSES else {})},
		fields=CONVERSATION_FIELDS,
		order_by="last_message_at desc",
		start=cint(start),
		page_length=min(cint(page_length) or 50, MAX_PAGE_LENGTH),
	)
	return {"conversations": [__conversation(row) for row in rows], "counts": __counts(filters)}


def get_conversation(phone_number: str, before: str | None = None, limit: int = 50) -> dict:
	"""
	Return one conversation with its latest messages, oldest first.

	Parameters:
	        phone_number (str, required): The customer's number.
	        before (str, optional): Only messages created before this time (older pages).
	        limit (int, optional): Messages to return, at most 100.

	Returns:
	        dict: {"conversation": {...}, "messages": [...], "reference": {"doctype", "name"} | None}
	"""
	check_access("read")
	number = get_profile_name(phone_number)
	row = frappe.db.get_value("WhatsApp Profile", number, CONVERSATION_FIELDS, as_dict=True)
	return {
		"conversation": __conversation(row),
		"messages": get_message_rows(number, before, min(cint(limit) or 50, MAX_PAGE_LENGTH)),
		"reference": get_reference(number),
	}


def mark_read(phone_number: str) -> None:
	"""
	Set the unread count of a conversation to zero.

	Parameters:
	        phone_number (str, required): The customer's number.

	Returns:
	        None
	"""
	check_access("read")
	frappe.db.set_value(
		"WhatsApp Profile", get_profile_name(phone_number), "unread_count", 0, update_modified=False
	)


def set_status(phone_number: str, status: str) -> None:
	"""
	Set a conversation to Open, Pending or Closed.

	Parameters:
	        phone_number (str, required): The customer's number.
	        status (str, required): "Open", "Pending" or "Closed".

	Returns:
	        None
	"""
	check_access("write")
	if status not in STATUSES:
		frappe.throw(_("Status must be one of {0}").format(", ".join(STATUSES)))
	frappe.db.set_value(
		"WhatsApp Profile", get_profile_name(phone_number), "conversation_status", status
	)


def get_profile_name(phone_number: str) -> str:
	"""
	Return the WhatsApp Profile of a number, or stop when there is none.

	Parameters:
	        phone_number (str, required): The customer's number in any format.

	Returns:
	        str: The WhatsApp Profile name.
	"""
	number = normalize_number(phone_number)
	if not number or not frappe.db.exists("WhatsApp Profile", number):
		frappe.throw(
			_("No WhatsApp conversation with {0}").format(phone_number), frappe.DoesNotExistError
		)
	return number


def check_access(permission: str) -> None:
	"""
	Stop users who cannot read (or write) WhatsApp Messages.

	Parameters:
	        permission (str, required): "read" or "write".

	Returns:
	        None
	"""
	frappe.has_permission("WhatsApp Message", permission, throw=True)


def __conversation(row) -> dict:
	"""
	Add the reply window and the assignee's name to a profile row.

	Parameters:
	        row (dict, required): A WhatsApp Profile row with CONVERSATION_FIELDS.

	Returns:
	        dict: The row with phone_number, display_name, the reply window and assigned_to_name.
	"""
	expires_at = None
	if row.last_incoming_at:
		expires_at = add_to_date(get_datetime(row.last_incoming_at), hours=WINDOW_HOURS)
	minutes_left = int((expires_at - now_datetime()).total_seconds() // 60) if expires_at else 0
	return {
		**row,
		"phone_number": row.name,
		"display_name": row.profile_name or row.name,
		"window_open": minutes_left > 0,
		"window_expires_at": expires_at,
		"window_minutes_left": max(minutes_left, 0),
		"assigned_to_name": frappe.utils.get_fullname(row.assigned_to) if row.assigned_to else None,
	}


def __filters(assigned_to: str | None, account: str | None, search: str | None) -> dict:
	"""
	Build the profile filters shared by the list and the tab counts.

	Parameters:
	        assigned_to (str, optional): A user, "me" or "unassigned".
	        account (str, optional): A WhatsApp Account.
	        search (str, optional): Part of the number or the WhatsApp name.

	Returns:
	        dict: Filters for frappe.get_all.
	"""
	filters = {"conversation_status": ["is", "set"]}
	if assigned_to == "me":
		filters["assigned_to"] = frappe.session.user
	elif assigned_to == "unassigned":
		filters["assigned_to"] = ["is", "not set"]
	elif assigned_to:
		filters["assigned_to"] = assigned_to
	if account:
		filters["whatsapp_account"] = account
	if search:
		text = search.strip()
		digits = re.sub(r"[\s+\-()]", "", text)
		if digits.isdigit():
			filters["name"] = ["like", f"%{digits}%"]
		else:
			filters["profile_name"] = ["like", f"%{text}%"]
	return filters


def __counts(filters: dict) -> dict:
	"""
	Count the conversations of each status for the given filters.

	Parameters:
	        filters (dict, required): The list filters without the status.

	Returns:
	        dict: {"Open": n, "Pending": n, "Closed": n}
	"""
	return {
		status: frappe.db.count("WhatsApp Profile", {**filters, "conversation_status": status})
		for status in STATUSES
	}
