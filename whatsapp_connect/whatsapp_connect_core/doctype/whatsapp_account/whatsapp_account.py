# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_account.account_utils import (
	clear_other_defaults,
	validate_account,
)


class WhatsAppAccount(Document):
	"""A WhatsApp Business phone number connected through a Meta app."""

	def validate(self):
		"""
		Check the Graph API settings before saving.

		Returns:
		        None
		"""
		validate_account(self)

	def on_update(self):
		"""
		Keep one default account per direction.

		Returns:
		        None
		"""
		clear_other_defaults(self)
