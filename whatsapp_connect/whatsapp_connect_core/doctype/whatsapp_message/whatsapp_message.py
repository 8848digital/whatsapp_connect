# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_message.message_utils import (
	prepare_message,
	send_after_insert,
)


class WhatsAppMessage(Document):
	"""One WhatsApp message, sent or received."""

	def before_insert(self):
		"""
		Fill the account, number, status, profile and reference.

		Returns:
		        None
		"""
		prepare_message(self)

	def after_insert(self):
		"""
		Send an outgoing message once it is saved, so a failed send is kept for retry.

		Returns:
		        None
		"""
		send_after_insert(self)
