# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Business logic for WhatsApp Recipient List."""

import json

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_utils import (
	split_lines,
)
from whatsapp_connect.whatsapp_connect_core.messaging.template_params import field_value
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number

VARIABLE_SEPARATOR = "|"


def clean_recipients(recipient_list) -> None:
	"""
	Normalize the numbers; drop rows with an invalid number and repeated numbers.

	Parameters:
	        recipient_list (Document, required): The WhatsApp Recipient List being saved.

	Returns:
	        None
	"""
	seen = set()
	rows = []
	for row in recipient_list.recipients:
		number = normalize_number(row.phone_number)
		if not number or number in seen:
			continue
		seen.add(number)
		row.phone_number = number
		rows.append(row)
	recipient_list.set("recipients", rows)
	recipient_list.recipient_count = len(rows)


def import_recipients(list_name: str) -> int:
	"""
	Add the records of the list's source doctype as recipients.

	Uses the list's Document Type, Phone Field, Name Field, Variable Fields,
	Filters and Maximum Records. Numbers already on the list are kept once.

	Parameters:
	        list_name (str, required): The WhatsApp Recipient List name.

	Returns:
	        int: The number of recipients after the import.
	"""
	recipient_list = frappe.get_doc("WhatsApp Recipient List", list_name)
	recipient_list.check_permission("write")
	if not (recipient_list.source_doctype and recipient_list.phone_field):
		frappe.throw(_("Set the Document Type and the Phone Field to import"))
	frappe.has_permission(recipient_list.source_doctype, "read", throw=True)

	filters = json.loads(recipient_list.import_filters) if recipient_list.import_filters else {}
	names = frappe.get_list(
		recipient_list.source_doctype,
		filters=filters,
		pluck="name",
		limit=recipient_list.import_limit or 1000,
	)
	variable_fields = split_lines(recipient_list.variable_fields)
	for name in names:
		doc = frappe.get_doc(recipient_list.source_doctype, name)
		if not doc.get(recipient_list.phone_field):
			continue
		recipient_list.append(
			"recipients",
			{
				"phone_number": doc.get(recipient_list.phone_field),
				"recipient_name": doc.get(recipient_list.name_field) if recipient_list.name_field else None,
				"variables": VARIABLE_SEPARATOR.join(
					field_value(doc, field) or "" for field in variable_fields
				),
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
			},
		)
	recipient_list.save()
	return recipient_list.recipient_count
