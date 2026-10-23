# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Find the Contact, Lead or Customer that a phone number belongs to."""

import frappe
from frappe.query_builder.functions import Function

from whatsapp_connect.whatsapp_connect_core.phone import number_suffix

# Doctypes and phone fields, in the order they are searched. Doctypes or
# fields missing on the site (for example Lead without ERPNext) are skipped.
PARTY_PHONE_FIELDS = (
	("Lead", ("mobile_no", "whatsapp_no", "phone")),
	("Customer", ("mobile_no",)),
)
# Doctypes whose timeline also shows the messages of their linked contacts.
PARTY_DOCTYPES = ("Customer", "Supplier", "Lead")
STRIPPED_CHARACTERS = (" ", "-", "(", ")", "+", ".")


def find_reference(number: str | None) -> tuple[str | None, str | None]:
	"""
	Return the first record that has this number: a Contact, then a Lead, then a Customer.

	Numbers match on their last 10 digits, so the stored format does not matter.

	Parameters:
	        number (str, optional): A phone number in any format.

	Returns:
	        tuple: (doctype, name), or (None, None) when nothing matches.
	"""
	suffix = number_suffix(number)
	if not suffix:
		return None, None

	contact = find_contact(suffix)
	if contact:
		return "Contact", contact

	for doctype, fields in PARTY_PHONE_FIELDS:
		name = __find_by_fields(doctype, fields, suffix)
		if name:
			return doctype, name
	return None, None


def find_contact(suffix: str) -> str | None:
	"""
	Find a Contact by its phone table or its mobile and phone fields.

	Parameters:
	        suffix (str, required): The last digits of the number.

	Returns:
	        str | None: The Contact name.
	"""
	phone = frappe.qb.DocType("Contact Phone")
	matches = (
		frappe.qb.from_(phone)
		.select(phone.parent)
		.where(phone.parenttype == "Contact")
		.where(__digits_only(phone.phone).like(f"%{suffix}"))
		.limit(1)
		.run(pluck=True)
	)
	if matches:
		return matches[0]
	return __find_by_fields("Contact", ("mobile_no", "phone"), suffix)


def get_linked_contacts(doctype: str, name: str) -> list[str]:
	"""
	Return the contacts linked to a Customer, Supplier or Lead.

	Parameters:
	        doctype (str, required): The party doctype.
	        name (str, required): The party name.

	Returns:
	        list[str]: Contact names; empty for other doctypes.
	"""
	if doctype not in PARTY_DOCTYPES:
		return []
	return frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "Contact", "link_doctype": doctype, "link_name": name},
		pluck="parent",
	)


def __find_by_fields(doctype: str, fields: tuple, suffix: str) -> str | None:
	"""
	Search a doctype's phone fields for a number suffix.

	Parameters:
	        doctype (str, required): The doctype to search.
	        fields (tuple, required): Phone fieldnames to try, in order.
	        suffix (str, required): The last digits of the number.

	Returns:
	        str | None: The first matching record name.
	"""
	if not frappe.db.exists("DocType", doctype):
		return None
	meta = frappe.get_meta(doctype)
	table = frappe.qb.DocType(doctype)
	for fieldname in (field for field in fields if meta.has_field(field)):
		matches = (
			frappe.qb.from_(table)
			.select(table.name)
			.where(__digits_only(table[fieldname]).like(f"%{suffix}"))
			.limit(1)
			.run(pluck=True)
		)
		if matches:
			return matches[0]
	return None


def __digits_only(column):
	"""
	Wrap a column so that spaces, dashes, brackets, dots and "+" are removed in SQL.

	Parameters:
	        column (Field, required): A query builder column.

	Returns:
	        Term: The column expression without those characters.
	"""
	for character in STRIPPED_CHARACTERS:
		column = Function("REPLACE", column, character, "")
	return column
