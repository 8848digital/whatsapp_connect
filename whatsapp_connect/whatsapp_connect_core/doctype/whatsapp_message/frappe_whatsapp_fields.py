# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Read-only names of the frappe_whatsapp app for WhatsApp Message.

Frappe CRM adds doc_events to "WhatsApp Message" that read doc.type and
doc.message (the field names of the frappe_whatsapp app). Without these names,
every message save fails when Frappe CRM is installed.
"""


class FrappeWhatsAppFields:
	"""Mixin for WhatsApp Message: type and message, as frappe_whatsapp names them."""

	@property
	def type(self) -> str | None:
		"""
		The direction, as frappe_whatsapp's "type" field.

		Returns:
		        str | None: "Incoming" or "Outgoing".
		"""
		return self.direction

	@property
	def message(self) -> str | None:
		"""
		The text, as frappe_whatsapp's "message" field.

		Returns:
		        str | None: The message body.
		"""
		return self.body
