# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Create a Lead when a number that matches no record writes (WhatsApp Settings > Lead Capture)."""

import frappe
from frappe import _
from frappe.utils import cint

from whatsapp_connect.whatsapp_connect_core.messaging.conversation import message_preview

# Lead doctypes and their fields. ERPNext 16 moved the source to utm_source.
LEAD_FIELDS = {
	"Lead": {"name": "first_name", "phones": ("mobile_no", "whatsapp_no")},
	"CRM Lead": {"name": "first_name", "phones": ("mobile_no",)},
}
SOURCE_FIELDS = ("source", "utm_source")


def handle_incoming(message) -> None:
	"""
	Create a Lead for an incoming message from an unknown number, and link the message to it.

	The message is unknown when no Contact, Lead or Customer has its number; the
	next message from the number then finds the new Lead, so no duplicate is made.

	Parameters:
	        message (Document, required): The saved incoming WhatsApp Message.

	Returns:
	        None
	"""
	settings = get_settings()
	if not cint(settings.get("create_leads")) or message.reference_doctype:
		return
	doctype = settings.get("lead_doctype") or "Lead"
	if doctype not in LEAD_FIELDS or not frappe.db.exists("DocType", doctype):
		return

	lead = create_lead(doctype, message, settings)
	message.db_set({"reference_doctype": doctype, "reference_name": lead.name}, update_modified=False)
	if settings.get("lead_owner") and not frappe.db.get_value(
		"WhatsApp Profile", message.profile, "assigned_to"
	):
		frappe.db.set_value("WhatsApp Profile", message.profile, "assigned_to", settings.lead_owner)


def get_settings() -> dict:
	"""
	Return the values of WhatsApp Settings, read from the database.

	Returns:
	        dict: The settings, for example {"create_leads": "1", "lead_doctype": "Lead"}.
	"""
	return frappe._dict(frappe.db.get_singles_dict("WhatsApp Settings"))


def create_lead(doctype: str, message, settings):
	"""
	Insert the Lead with the sender's WhatsApp name, number, source and owner.

	Parameters:
	        doctype (str, required): "Lead" (ERPNext) or "CRM Lead" (Frappe CRM).
	        message (Document, required): The incoming WhatsApp Message.
	        settings (dict, required): The values of WhatsApp Settings.

	Returns:
	        Document: The new Lead.
	"""
	fields = LEAD_FIELDS[doctype]
	meta = frappe.get_meta(doctype)
	profile_name = frappe.db.get_value("WhatsApp Profile", message.profile, "profile_name")
	values = {"doctype": doctype, fields["name"]: profile_name or f"WhatsApp +{message.phone_number}"}
	for fieldname in fields["phones"]:
		if meta.has_field(fieldname):
			values[fieldname] = f"+{message.phone_number}"
	if settings.get("lead_owner") and meta.has_field("lead_owner"):
		values["lead_owner"] = settings.lead_owner
	source_field = next((field for field in SOURCE_FIELDS if meta.has_field(field)), None)
	if source_field and settings.get("lead_source"):
		values[source_field] = __get_or_create_source(
			meta.get_field(source_field).options, settings.lead_source
		)

	lead = frappe.get_doc(values)
	lead.flags.ignore_mandatory = True
	lead.insert(ignore_permissions=True)
	lead.add_comment(
		"Comment",
		_("Created from a WhatsApp message: {0}").format(
			frappe.utils.escape_html(message_preview(message))
		),
	)
	return lead


def __get_or_create_source(doctype: str, value: str) -> str:
	"""
	Return the source record (Lead Source, UTM Source or CRM Lead Source), creating it once.

	Parameters:
	        doctype (str, required): The doctype the source field links to.
	        value (str, required): The source name, for example "WhatsApp".

	Returns:
	        str: The record name.
	"""
	if frappe.db.exists(doctype, value):
		return value
	autoname = frappe.get_meta(doctype).autoname or ""
	doc = frappe.new_doc(doctype)
	if autoname.startswith("field:"):
		doc.set(autoname[len("field:") :], value)
		doc.insert(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True, set_name=value)
	return doc.name
