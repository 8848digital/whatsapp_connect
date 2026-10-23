# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Background jobs that send a campaign's messages."""

import time

import frappe
from frappe.utils import now_datetime

from whatsapp_connect.whatsapp_connect_campaign.doctype.whatsapp_campaign.campaign_utils import (
	build_values,
	refresh_counts,
)
from whatsapp_connect.whatsapp_connect_core.cloud_api import RATE_LIMIT_CODES
from whatsapp_connect.whatsapp_connect_core.messaging import sender
from whatsapp_connect.whatsapp_connect_core.messaging.template_send import send_template

MAX_ATTEMPTS = 3
FIRST_WAIT_SECONDS = 2
# Replaced in tests, so retries do not wait.
sleep = time.sleep


def send_batch(campaign_name: str, recipients: list[dict]) -> None:
	"""
	Send the campaign's template to a batch of recipients.

	Stops when the campaign is cancelled. Messages that Meta refuses because of
	a rate limit are sent again after a growing wait.

	Parameters:
	        campaign_name (str, required): The WhatsApp Campaign name.
	        recipients (list[dict], required): Recipients from get_recipients.

	Returns:
	        None
	"""
	campaign = frappe.get_doc("WhatsApp Campaign", campaign_name)
	for recipient in recipients:
		if frappe.db.get_value("WhatsApp Campaign", campaign_name, "status") == "Cancelled":
			return
		message = send_template(
			campaign.template,
			recipient["phone_number"],
			doc=__reference(recipient),
			values=build_values(campaign, recipient),
			account=campaign.whatsapp_account,
			source=f"Campaign: {campaign_name}",
			campaign=campaign_name,
		)
		__retry_rate_limited(message)
		if not frappe.flags.in_test:
			frappe.db.commit()  # nosemgrep: frappe-manual-commit -- background job: keep each sent message even if a later one fails
	finish_if_done(campaign_name)


def retry_failed(campaign_name: str) -> int:
	"""
	Send the campaign's failed messages again.

	Parameters:
	        campaign_name (str, required): The WhatsApp Campaign name.

	Returns:
	        int: The number of messages that Meta accepted this time.
	"""
	sent = 0
	for name in frappe.get_all(
		"WhatsApp Message", filters={"campaign": campaign_name, "status": "Failed"}, pluck="name"
	):
		sent += sender.send(frappe.get_doc("WhatsApp Message", name))
	finish_if_done(campaign_name)
	return sent


def finish_if_done(campaign_name: str) -> None:
	"""
	Close the campaign once every recipient has a message: Completed or Partially Failed.

	Parameters:
	        campaign_name (str, required): The WhatsApp Campaign name.

	Returns:
	        None
	"""
	counts = refresh_counts(campaign_name)
	campaign = frappe.db.get_value(
		"WhatsApp Campaign", campaign_name, ["status", "total_recipients"], as_dict=True
	)
	created = frappe.db.count("WhatsApp Message", {"campaign": campaign_name})
	if campaign.status == "Cancelled" or created < (campaign.total_recipients or 0):
		return
	status = "Partially Failed" if counts["failed_count"] else "Completed"
	frappe.db.set_value(
		"WhatsApp Campaign", campaign_name, {"status": status, "completed_at": now_datetime()}
	)


def __retry_rate_limited(message) -> None:
	"""
	Send a rate-limited message again, waiting 2, then 4 seconds.

	Parameters:
	        message (Document, required): The WhatsApp Message just sent.

	Returns:
	        None
	"""
	for attempt in range(1, MAX_ATTEMPTS):
		message.reload()
		if (
			message.status != "Failed"
			or not message.error_code
			or int(message.error_code) not in RATE_LIMIT_CODES
		):
			return
		sleep(FIRST_WAIT_SECONDS * 2 ** (attempt - 1))
		sender.send(message)


def __reference(recipient: dict):
	"""
	Load the recipient's document, which fills mapped variables and is linked to the message.

	Parameters:
	        recipient (dict, required): A recipient from get_recipients.

	Returns:
	        Document | None: The document, or None.
	"""
	doctype, name = recipient.get("reference_doctype"), recipient.get("reference_name")
	if doctype and name and frappe.db.exists(doctype, name):
		return frappe.get_doc(doctype, name)
	return None
