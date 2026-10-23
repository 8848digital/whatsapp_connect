# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""The mobile number of a document's party (customer or supplier) or contact person.

Payment Entry, Payment Request and similar documents have a party but no
mobile number field.
"""

import frappe

from whatsapp_connect.whatsapp_connect_core.phone import normalize_number

# (party type field, party field); a missing type field means the field name is the type.
PARTY_FIELDS = (("party_type", "party"), (None, "customer"), (None, "supplier"))


def get_party_number(doc) -> str | None:
	"""
	Return the first mobile number found for the document's contact or party.

	Order: Contact Mobile on the document, the Contact Person, the party's own
	Mobile No, its primary contact, then any contact linked to it.

	Parameters:
	        doc (Document | dict, required): The document.

	Returns:
	        str | None: Digits-only number, or None.
	"""
	number = normalize_number(doc.get("contact_mobile"))
	if number:
		return number
	if doc.get("contact_person"):
		number = contact_number(doc.get("contact_person"))
		if number:
			return number
	for type_field, name_field in PARTY_FIELDS:
		party_type = doc.get(type_field) if type_field else name_field.title()
		if party_type and doc.get(name_field):
			number = party_number(party_type, doc.get(name_field))
			if number:
				return number
	return None


def contact_number(contact: str) -> str | None:
	"""
	Return a contact's mobile number: Mobile No, Phone, then its phone table.

	Parameters:
	        contact (str, required): The Contact name.

	Returns:
	        str | None: Digits-only number, or None.
	"""
	values = frappe.db.get_value("Contact", contact, ["mobile_no", "phone"], as_dict=True) or {}
	for value in (values.get("mobile_no"), values.get("phone")):
		if normalize_number(value):
			return normalize_number(value)
	phones = frappe.get_all(
		"Contact Phone",
		filters={"parent": contact, "parenttype": "Contact"},
		fields=["phone"],
		order_by="is_primary_mobile_no desc, idx asc",
	)
	return next((normalize_number(row.phone) for row in phones if normalize_number(row.phone)), None)


def party_number(party_type: str, party: str) -> str | None:
	"""
	Return the number of a Customer or Supplier, or of its contacts.

	Parameters:
	        party_type (str, required): "Customer" or "Supplier".
	        party (str, required): The party name.

	Returns:
	        str | None: Digits-only number, or None.
	"""
	if not frappe.db.exists("DocType", party_type) or not frappe.db.exists(party_type, party):
		return None
	meta = frappe.get_meta(party_type)
	if meta.has_field("mobile_no"):
		number = normalize_number(frappe.db.get_value(party_type, party, "mobile_no"))
		if number:
			return number
	contacts = []
	primary_field = f"{frappe.scrub(party_type)}_primary_contact"
	if meta.has_field(primary_field):
		contacts.append(frappe.db.get_value(party_type, party, primary_field))
	contacts += frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "Contact", "link_doctype": party_type, "link_name": party},
		pluck="parent",
	)
	return next(
		(contact_number(contact) for contact in contacts if contact and contact_number(contact)), None
	)
