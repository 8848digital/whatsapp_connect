# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_campaign.doctype.whatsapp_recipient_list.recipient_list_utils import (
	clean_recipients,
)


class WhatsAppRecipientList(Document):
	"""A reusable list of numbers for campaigns."""

	def validate(self):
		"""
		Normalize the numbers, drop invalid ones and duplicates, and count them.

		Returns:
		        None
		"""
		clean_recipients(self)
