# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_campaign.doctype.whatsapp_campaign.campaign_utils import (
	cancel_campaign,
	submit_campaign,
	validate_campaign,
)


class WhatsAppCampaign(Document):
	"""Sends one template to many recipients, now or at a set time."""

	def validate(self):
		"""
		Check the template, recipients and send time; count the recipients.

		Returns:
		        None
		"""
		validate_campaign(self)

	def on_submit(self):
		"""
		Start sending, or schedule the campaign.

		Returns:
		        None
		"""
		submit_campaign(self)

	def on_cancel(self):
		"""
		Stop sending the messages that are not sent yet.

		Returns:
		        None
		"""
		cancel_campaign(self)
