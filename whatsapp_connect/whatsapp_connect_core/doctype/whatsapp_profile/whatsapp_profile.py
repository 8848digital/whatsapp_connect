# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_profile.profile_utils import (
	validate_profile,
)


class WhatsAppProfile(Document):
	"""One WhatsApp user (phone number) and their opt-out state."""

	def before_insert(self):
		"""
		Normalize the number before the profile is named after it.

		Returns:
		        None
		"""
		validate_profile(self)

	def validate(self):
		"""
		Store the number in the digits-only form.

		Returns:
		        None
		"""
		validate_profile(self)
