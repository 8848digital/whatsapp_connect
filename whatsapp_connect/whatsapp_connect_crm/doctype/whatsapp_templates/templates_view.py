# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Approved WhatsApp Templates with the field names of frappe_whatsapp's "WhatsApp Templates"."""

import frappe
from frappe import _

FIELDS = ["name", "template_name", "body", "footer", "modified", "creation", "owner"]


def list_templates() -> list[dict]:
	"""
	Return the approved templates, newest first. Read access is checked on WhatsApp Templates.

	Returns:
	        list[dict]: Rows with name, template_name, template (the body), footer, status and for_doctype.
	"""
	rows = frappe.get_all(
		"WhatsApp Template", filters={"status": "Approved"}, fields=FIELDS, order_by="modified desc"
	)
	return [__row(row) for row in rows]


def count_templates() -> int:
	"""
	Return the number of approved templates.

	Returns:
	        int: The count.
	"""
	return len(frappe.get_all("WhatsApp Template", filters={"status": "Approved"}, pluck="name"))


def load_template(name: str) -> dict:
	"""
	Return one approved template as a document dict.

	Parameters:
	        name (str, required): The WhatsApp Template name.

	Returns:
	        dict: The values of the virtual document.
	"""
	rows = frappe.get_all("WhatsApp Template", filters={"name": name}, fields=FIELDS)
	if not rows:
		frappe.throw(_("WhatsApp Template {0} not found").format(name), frappe.DoesNotExistError)
	return {"doctype": "WhatsApp Templates", **__row(rows[0])}


def __row(row: dict) -> dict:
	"""
	Rename the fields of a WhatsApp Template row.

	Parameters:
	        row (dict, required): A WhatsApp Template row.

	Returns:
	        dict: The row with frappe_whatsapp field names.
	"""
	return {
		"name": row.name,
		"template_name": row.template_name,
		"template": row.body,
		"footer": row.footer,
		"status": "APPROVED",
		"for_doctype": "",
		"modified": row.modified,
		"creation": row.creation,
		"owner": row.owner,
	}
