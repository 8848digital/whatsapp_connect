# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_campaign import campaign_sender
from whatsapp_connect.whatsapp_connect_campaign.doctype.whatsapp_campaign.campaign_utils import (
	refresh_counts,
)


@frappe.whitelist(methods=["POST"])
def refresh(campaign: str):
	"""
	        Count a campaign's messages by status (sent, delivered, read, failed, opted out)
	        and store the counts on the campaign.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_campaign.api.v1.campaign.refresh`
	        **HTTP Method:** POST
	        **Parameters:**
	                - campaign (str, required): The WhatsApp Campaign name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "",
	                        "data": {"sent_count": 95, "delivered_count": 90, "read_count": 60, "failed_count": 3, "opted_out_count": 2},
	                        "errors": null
	                }
	```
	"""
	frappe.get_doc("WhatsApp Campaign", campaign).check_permission("read")
	return api_response(data=refresh_counts(campaign))


@frappe.whitelist(methods=["POST"])
def retry_failed(campaign: str):
	"""
	        Send the failed messages of a campaign again, in a background job.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_campaign.api.v1.campaign.retry_failed`
	        **HTTP Method:** POST
	        **Parameters:**
	                - campaign (str, required): The WhatsApp Campaign name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "The failed messages are being sent again",
	                        "data": null,
	                        "errors": null
	                }
	```
	"""
	frappe.get_doc("WhatsApp Campaign", campaign).check_permission("write")
	frappe.enqueue(
		"whatsapp_connect.whatsapp_connect_campaign.campaign_sender.retry_failed",
		queue="long",
		now=bool(frappe.flags.in_test),
		campaign_name=campaign,
	)
	return api_response(message=_("The failed messages are being sent again"))
