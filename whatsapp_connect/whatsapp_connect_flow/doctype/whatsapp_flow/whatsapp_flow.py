# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_flow.doctype.whatsapp_flow.flow_json import validate_flow
from whatsapp_connect.whatsapp_connect_flow.doctype.whatsapp_flow.flow_meta import delete_in_meta


class WhatsAppFlow(Document):
	"""A WhatsApp Flow: screens of forms that the customer fills inside WhatsApp."""

	def validate(self):
		"""
		Check the screens and components and build the Flow JSON.

		Returns:
		        None
		"""
		validate_flow(self)

	def on_trash(self):
		"""
		Delete a draft flow in Meta too.

		Returns:
		        None
		"""
		delete_in_meta(self)
