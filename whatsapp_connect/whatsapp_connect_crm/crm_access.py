# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Who may use WhatsApp in Frappe CRM, and the numbers of a CRM Lead or Deal."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.phone import normalize_number

CRM_ROLES = ("System Manager", "Sales Manager", "Sales User", "WhatsApp Manager", "WhatsApp User")
PHONE_FIELDS = ("mobile_no", "phone")


def check_access(
	reference_doctype: str | None = None, reference_name: str | None = None, permtype: str = "read"
):
	"""
	Stop users without a sales or WhatsApp role, or who cannot open the record.

	Parameters:
	        reference_doctype (str, optional): The CRM Lead, CRM Deal or other record type.
	        reference_name (str, optional): The record name.
	        permtype (str, optional): The permission needed on the record. Default "read".

	Returns:
	        Document | None: The record, when one is given.
	"""
	if not set(frappe.get_roles()) & set(CRM_ROLES):
		frappe.throw(_("Only sales users can use WhatsApp"), frappe.PermissionError)
	if not (reference_doctype and reference_name):
		return None
	doc = frappe.get_doc(reference_doctype, reference_name)
	doc.check_permission(permtype)
	return doc


def get_numbers(doc) -> list[str]:
	"""
	Return the WhatsApp numbers of a record: its phone fields, its contacts and its lead.

	Parameters:
	        doc (Document, required): A CRM Lead, CRM Deal or other record.

	Returns:
	        list[str]: Digits-only numbers without duplicates.
	"""
	values = [doc.get(field) for field in PHONE_FIELDS]
	contacts = [row.contact for row in doc.get("contacts") or [] if row.get("contact")]
	if doc.get("contact"):
		contacts.append(doc.contact)
	if contacts:
		values += frappe.get_all(
			"Contact Phone", filters={"parenttype": "Contact", "parent": ["in", contacts]}, pluck="phone"
		)
	if doc.doctype == "CRM Deal" and doc.get("lead"):
		values += frappe.db.get_value("CRM Lead", doc.lead, list(PHONE_FIELDS)) or []
	numbers = [normalize_number(value) for value in values]
	return list(dict.fromkeys(number for number in numbers if number))
