# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_automation.doctype.whatsapp_auto_reply.auto_reply_utils import (
	validate_rule,
)


class WhatsAppAutoReply(Document):
	"""A rule that answers incoming WhatsApp messages automatically."""

	def validate(self):
		"""
		Check the keywords, the options and the action, and fill missing option IDs.

		Returns:
		        None
		"""
		validate_rule(self)
