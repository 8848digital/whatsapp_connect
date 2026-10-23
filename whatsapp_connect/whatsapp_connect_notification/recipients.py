# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Who receives a WhatsApp Notification."""

import frappe

from whatsapp_connect.whatsapp_connect_core.messaging.opt_out import filter_opted_out
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number
from whatsapp_connect.whatsapp_connect_notification.doctype.whatsapp_notification.notification_utils import (
	condition_is_true,
)
from whatsapp_connect.whatsapp_connect_notification.party_phone import get_party_number


def get_recipient_numbers(notification, doc=None) -> list[str]:
	"""
	Collect the numbers from all recipient sources, without duplicates and opted-out numbers.

	Parameters:
	        notification (Document, required): The WhatsApp Notification.
	        doc (Document, optional): The document; None for scheduled notifications without one.

	Returns:
	        list[str]: Digits-only numbers, in the order found.
	"""
	numbers = []
	if doc is not None and notification.phone_field:
		numbers.append(normalize_number(doc.get(notification.phone_field)))
	if doc is not None and notification.send_to_party:
		numbers.append(get_party_number(doc))
	numbers += [normalize_number(line) for line in (notification.fixed_numbers or "").splitlines()]
	numbers += get_role_numbers(notification.recipient_roles, doc)

	unique = list(dict.fromkeys(number for number in numbers if number))
	allowed, _opted_out = filter_opted_out(unique)
	return allowed


def get_role_numbers(role_rows: list, doc=None) -> list[str]:
	"""
	Return the numbers of enabled users with the roles whose condition is true.

	Parameters:
	        role_rows (list, required): WhatsApp Notification Role rows.
	        doc (Document, optional): The document the conditions are checked against.

	Returns:
	        list[str]: Digits-only numbers of those users.
	"""
	roles = [row.role for row in role_rows if condition_is_true(row.condition, doc)]
	if not roles:
		return []
	users = frappe.get_all(
		"Has Role",
		filters={
			"role": ["in", roles],
			"parenttype": "User",
			"parent": ["not in", ["Administrator", "Guest"]],
		},
		pluck="parent",
		distinct=True,
	)
	enabled = frappe.get_all(
		"User", filters={"name": ["in", users or [""]], "enabled": 1}, pluck="name"
	)
	return [number for number in (user_number(user) for user in enabled) if number]


def user_number(user: str) -> str | None:
	"""
	Return a user's number from the source set in WhatsApp Settings.

	Parameters:
	        user (str, required): The User name.

	Returns:
	        str | None: Digits-only number, or None.
	"""
	source = frappe.db.get_single_value("WhatsApp Settings", "role_phone_source") or "User Mobile No"
	readers = {
		"User Mobile No": (__user_mobile,),
		"Employee Cell Number": (__employee_mobile,),
		"User, then Employee": (__user_mobile, __employee_mobile),
		"Employee, then User": (__employee_mobile, __user_mobile),
	}[source]
	return next((number for number in (reader(user) for reader in readers) if number), None)


def __user_mobile(user: str) -> str | None:
	"""
	Mobile No on the User.

	Parameters:
	        user (str, required): The User name.

	Returns:
	        str | None: Digits-only number.
	"""
	return normalize_number(frappe.db.get_value("User", user, "mobile_no"))


def __employee_mobile(user: str) -> str | None:
	"""
	Cell Number of the Employee linked to the user (HRMS or ERPNext).

	Parameters:
	        user (str, required): The User name.

	Returns:
	        str | None: Digits-only number, or None without an Employee doctype.
	"""
	if not frappe.db.exists("DocType", "Employee"):
		return None
	return normalize_number(
		frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "cell_number")
	)
