# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""One row per message of a campaign: number, status, times and Meta's error."""

import frappe
from frappe import _

FIELDS = [
	"name",
	"phone_number",
	"status",
	"sent_at",
	"delivered_at",
	"read_at",
	"error_code",
	"error_message",
]


def execute(filters=None):
	"""
	Report entry point.

	Parameters:
	        filters (dict, optional): campaign (required) and status.

	Returns:
	        tuple: (columns, data)
	"""
	filters = frappe._dict(filters or {})
	if not filters.get("campaign"):
		return get_columns(), []
	conditions = {"campaign": filters.campaign}
	if filters.get("status"):
		conditions["status"] = filters.status
	data = frappe.get_all(
		"WhatsApp Message", filters=conditions, fields=FIELDS, order_by="creation asc"
	)
	return get_columns(), data


def get_columns() -> list[dict]:
	"""
	Report columns.

	Returns:
	        list[dict]: Column definitions.
	"""
	return [
		{
			"label": _("Message"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "WhatsApp Message",
			"width": 120,
		},
		{"label": _("Phone Number"), "fieldname": "phone_number", "fieldtype": "Data", "width": 140},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Sent At"), "fieldname": "sent_at", "fieldtype": "Datetime", "width": 160},
		{"label": _("Delivered At"), "fieldname": "delivered_at", "fieldtype": "Datetime", "width": 160},
		{"label": _("Read At"), "fieldname": "read_at", "fieldtype": "Datetime", "width": 160},
		{"label": _("Error Code"), "fieldname": "error_code", "fieldtype": "Data", "width": 100},
		{"label": _("Error"), "fieldname": "error_message", "fieldtype": "Data", "width": 300},
	]
