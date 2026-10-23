# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Business logic for WhatsApp Campaign: validation, recipients, start and progress."""

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_utils import (
	split_lines,
)
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number

BATCH_SIZE = 50
STATUS_COUNTS = {
	"sent_count": ("Sent", "Delivered", "Read"),
	"delivered_count": ("Delivered", "Read"),
	"read_count": ("Read",),
	"failed_count": ("Failed",),
	"opted_out_count": ("Opted Out",),
}
MAX_PRODUCTS = 30


def validate_campaign(campaign) -> None:
	"""
	Check the campaign before saving and count its recipients.

	Parameters:
	        campaign (Document, required): The WhatsApp Campaign being saved.

	Returns:
	        None
	"""
	if frappe.db.get_value("WhatsApp Template", campaign.template, "status") != "Approved":
		frappe.throw(_("Template {0} is not approved by Meta").format(campaign.template))
	if (
		campaign.scheduled_at
		and campaign.docstatus == 0
		and get_datetime(campaign.scheduled_at) <= now_datetime()
	):
		frappe.throw(_("Send At must be in the future"))
	campaign.total_recipients = len(get_recipients(campaign))
	if not campaign.total_recipients:
		frappe.throw(_("Add at least one valid number"))


def get_recipients(campaign) -> list[dict]:
	"""
	Return the campaign's recipients with their variable values.

	Parameters:
	        campaign (Document, required): The WhatsApp Campaign.

	Returns:
	        list[dict]: {"phone_number", "variables", "reference_doctype", "reference_name"}, without duplicates.
	"""
	if campaign.recipient_source == "Recipient List":
		rows = frappe.get_all(
			"WhatsApp Recipient",
			filters={"parent": campaign.recipient_list, "parenttype": "WhatsApp Recipient List"},
			fields=["phone_number", "variables", "reference_doctype", "reference_name"],
			order_by="idx asc",
		)
	else:
		rows = [frappe._dict(phone_number=line) for line in split_lines(campaign.numbers)]

	recipients = {}
	for row in rows:
		number = normalize_number(row.phone_number)
		if number and number not in recipients:
			recipients[number] = {**row, "phone_number": number}
	return list(recipients.values())


def submit_campaign(campaign) -> None:
	"""
	Schedule the campaign, or start it now when it has no future send time.

	Parameters:
	        campaign (Document, required): The submitted WhatsApp Campaign.

	Returns:
	        None
	"""
	if campaign.scheduled_at and get_datetime(campaign.scheduled_at) > now_datetime():
		campaign.db_set("status", "Scheduled")
	else:
		start_campaign(campaign.name)


def start_campaign(campaign_name: str) -> None:
	"""
	Mark the campaign as Sending and queue its recipients in batches.

	Parameters:
	        campaign_name (str, required): The WhatsApp Campaign name.

	Returns:
	        None
	"""
	campaign = frappe.get_doc("WhatsApp Campaign", campaign_name)
	campaign.db_set({"status": "Sending", "started_at": now_datetime()})
	recipients = get_recipients(campaign)
	batches = [
		recipients[start : start + BATCH_SIZE] for start in range(0, len(recipients), BATCH_SIZE)
	]
	for batch in batches:
		frappe.enqueue(
			"whatsapp_connect.whatsapp_connect_campaign.campaign_sender.send_batch",
			queue="long",
			enqueue_after_commit=True,
			now=bool(frappe.flags.in_test),
			campaign_name=campaign_name,
			recipients=batch,
		)


def cancel_campaign(campaign) -> None:
	"""
	Mark the campaign Cancelled; batch jobs stop before the next message.

	Parameters:
	        campaign (Document, required): The cancelled WhatsApp Campaign.

	Returns:
	        None
	"""
	campaign.db_set("status", "Cancelled")


def refresh_counts(campaign_name: str) -> dict:
	"""
	Count the campaign's messages by status and store the counts on the campaign.

	Parameters:
	        campaign_name (str, required): The WhatsApp Campaign name.

	Returns:
	        dict: The counts, by field name.
	"""
	statuses = frappe.get_all(
		"WhatsApp Message",
		filters={"campaign": campaign_name},
		fields=["status", "count(name) as total"],
		group_by="status",
	)
	by_status = {row.status: row.total for row in statuses}
	counts = {
		field: sum(by_status.get(status, 0) for status in group)
		for field, group in STATUS_COUNTS.items()
	}
	frappe.db.set_value("WhatsApp Campaign", campaign_name, counts)
	return counts


def build_values(campaign, recipient: dict) -> dict:
	"""
	Template values for one recipient: variables, header file and catalog products.

	Parameters:
	        campaign (Document, required): The WhatsApp Campaign.
	        recipient (dict, required): A recipient from get_recipients.

	Returns:
	        dict: Values for send_template.
	"""
	values = {}
	if campaign.variable_mode == "Per Recipient" and recipient.get("variables"):
		values["body"] = [value.strip() for value in recipient["variables"].split("|")]
	elif split_lines(campaign.common_values):
		values["body"] = split_lines(campaign.common_values)
	if campaign.header_media:
		values["header_media"] = campaign.header_media
	action = __product_action(campaign)
	if action:
		template = frappe.get_cached_doc("WhatsApp Template", campaign.template)
		values["buttons"] = {}
		for index, button in enumerate(template.buttons):
			if button.button_type == "Multi-Product":
				values["buttons"][str(index)] = action
			elif button.button_type == "Catalog":
				# A catalog button shows the whole catalog; only the thumbnail is sent.
				values["buttons"][str(index)] = {
					"thumbnail_product_retailer_id": action["thumbnail_product_retailer_id"]
				}
	return values


def __product_action(campaign) -> dict | None:
	"""
	Build the action of a Catalog or Multi-Product button from the campaign's products.

	Parameters:
	        campaign (Document, required): The WhatsApp Campaign.

	Returns:
	        dict | None: The action object, or None when no products are set.
	"""
	products = split_lines(campaign.product_ids)[:MAX_PRODUCTS]
	thumbnail = campaign.thumbnail_product or (products[0] if products else None)
	if not thumbnail:
		return None
	action = {"thumbnail_product_retailer_id": thumbnail}
	if products:
		action["sections"] = [
			{
				"title": campaign.section_title or _("Products"),
				"product_items": [{"product_retailer_id": product} for product in products],
			}
		]
	return action
