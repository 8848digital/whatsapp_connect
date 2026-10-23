# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Delivery statuses of outgoing messages (sent, delivered, read, failed)."""

import frappe

from whatsapp_connect.whatsapp_connect_core.webhook.common import to_datetime

STATUS_MAP = {"sent": "Sent", "delivered": "Delivered", "read": "Read", "failed": "Failed"}
# Callbacks can arrive out of order; a status never moves back.
RANK = {"Queued": 0, "Sent": 1, "Delivered": 2, "Read": 3}
TIME_FIELDS = {"Sent": "sent_at", "Delivered": "delivered_at", "Read": "read_at"}


def update_statuses(statuses: list[dict]) -> None:
	"""
	Apply status callbacks to the messages sent from this site.

	Callbacks for messages sent elsewhere (Meta dashboard, other systems) are ignored.

	Parameters:
	        statuses (list[dict], required): Meta's status objects.

	Returns:
	        None
	"""
	for status in statuses:
		name = frappe.db.get_value(
			"WhatsApp Message", {"wamid": status.get("id"), "direction": "Outgoing"}
		)
		if name:
			__apply(name, status)


def __apply(name: str, status: dict) -> None:
	"""
	Update one message from one status callback.

	Parameters:
	        name (str, required): The WhatsApp Message name.
	        status (dict, required): Meta's status object.

	Returns:
	        None
	"""
	new_status = STATUS_MAP.get(status.get("status"))
	if not new_status:
		return
	current = frappe.db.get_value("WhatsApp Message", name, "status")
	values = {}
	if new_status == "Failed":
		error = (status.get("errors") or [{}])[0]
		details = (error.get("error_data") or {}).get("details")
		values.update(
			{
				"status": "Failed",
				"error_code": str(error.get("code") or ""),
				"error_message": " - ".join(
					part for part in (error.get("title") or error.get("message"), details) if part
				),
			}
		)
	elif RANK.get(new_status, 0) > RANK.get(current, -1) or current == "Failed":
		values["status"] = new_status

	if new_status in TIME_FIELDS:
		values[TIME_FIELDS[new_status]] = to_datetime(status.get("timestamp"))
	category = (status.get("pricing") or {}).get("category")
	if category:
		values["pricing_category"] = category
	if values:
		frappe.db.set_value("WhatsApp Message", name, values)
