# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Delivery of outgoing WhatsApp messages: sent, delivered, read, failed and opted out, with rates."""

import frappe
from frappe import _
from frappe.query_builder import Case
from frappe.query_builder.functions import Count, Date, Sum
from frappe.utils import add_days, flt, getdate, today

GROUPS = {
	"Template": "template",
	"Campaign": "campaign",
	"WhatsApp Account": "whatsapp_account",
	"Day": "creation",
}
# Meta reports sent, then delivered, then read: a read message was delivered and sent too.
SENT = ("Sent", "Delivered", "Read")
DELIVERED = ("Delivered", "Read")


def execute(filters=None):
	"""
	Report entry point.

	Parameters:
	        filters (dict, optional): from_date, to_date, group_by, whatsapp_account.

	Returns:
	        tuple: (columns, data, message, chart)
	"""
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	return get_columns(filters), data, None, get_chart(data)


def get_columns(filters) -> list[dict]:
	"""
	Report columns; the first one is named after the grouping.

	Parameters:
	        filters (dict, required): The report filters.

	Returns:
	        list[dict]: Column definitions.
	"""
	columns = [
		{
			"label": _(filters.get("group_by") or "Template"),
			"fieldname": "group",
			"fieldtype": "Data",
			"width": 220,
		}
	]
	for fieldname, label in (
		("total", "Total"),
		("sent", "Sent"),
		("delivered", "Delivered"),
		("read", "Read"),
		("failed", "Failed"),
		("opted_out", "Opted Out"),
	):
		columns.append({"label": _(label), "fieldname": fieldname, "fieldtype": "Int", "width": 100})
	columns.append(
		{"label": _("Delivery %"), "fieldname": "delivery_rate", "fieldtype": "Percent", "width": 110}
	)
	columns.append(
		{"label": _("Read %"), "fieldname": "read_rate", "fieldtype": "Percent", "width": 100}
	)
	return columns


def get_data(filters) -> list[dict]:
	"""
	Count the outgoing messages of the period by group and status.

	Parameters:
	        filters (dict, required): The report filters.

	Returns:
	        list[dict]: One row per group, largest first.
	"""
	message = frappe.qb.DocType("WhatsApp Message")
	field = GROUPS.get(filters.get("group_by") or "Template")
	group = Date(message.creation) if field == "creation" else message[field]
	from_date = getdate(filters.get("from_date") or add_days(today(), -30))
	to_date = getdate(filters.get("to_date") or today())

	def count(statuses):
		return Sum(Case().when(message.status.isin(statuses), 1).else_(0))

	query = (
		frappe.qb.from_(message)
		.select(
			group.as_("group"),
			Count(message.name).as_("total"),
			count(SENT).as_("sent"),
			count(DELIVERED).as_("delivered"),
			count(("Read",)).as_("read"),
			count(("Failed",)).as_("failed"),
			count(("Opted Out",)).as_("opted_out"),
		)
		.where(message.direction == "Outgoing")
		.where(Date(message.creation).between(from_date, to_date))
		.groupby(group)
		.orderby(Count(message.name), order=frappe.qb.desc)
	)
	if filters.get("whatsapp_account"):
		query = query.where(message.whatsapp_account == filters.whatsapp_account)

	rows = query.run(as_dict=True)
	for row in rows:
		row.group = str(row.group) if row.group else _("(not set)")
		row.delivery_rate = flt(row.delivered * 100 / row.sent, 1) if row.sent else 0
		row.read_rate = flt(row.read * 100 / row.delivered, 1) if row.delivered else 0
	return rows


def get_chart(data: list[dict]) -> dict | None:
	"""
	Bar chart of delivered, read and failed messages for the 10 largest groups.

	Parameters:
	        data (list[dict], required): The report rows.

	Returns:
	        dict | None: Frappe chart definition, or None without data.
	"""
	if not data:
		return None
	rows = data[:10]
	return {
		"data": {
			"labels": [row.group for row in rows],
			"datasets": [
				{"name": _("Delivered"), "values": [row.delivered for row in rows]},
				{"name": _("Read"), "values": [row.read for row in rows]},
				{"name": _("Failed"), "values": [row.failed for row in rows]},
			],
		},
		"type": "bar",
	}
