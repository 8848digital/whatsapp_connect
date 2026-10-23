# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_meta import (
	delete_in_meta,
)
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_utils import (
	validate_template,
)


class WhatsAppTemplate(Document):
	"""A WhatsApp message template, approved by Meta before it can be sent."""

	def before_insert(self):
		"""
		Normalize the name before the template is named after it.

		Returns:
		        None
		"""
		validate_template(self)

	def validate(self):
		"""
		Check the name, variables, samples and buttons.

		Returns:
		        None
		"""
		validate_template(self)

	def on_trash(self):
		"""
		Delete the template in Meta too.

		Returns:
		        None
		"""
		delete_in_meta(self)
