# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_crm.doctype.whatsapp_templates.templates_view import (
	count_templates,
	list_templates,
	load_template,
)


class WhatsAppTemplates(Document):
	"""Virtual, read-only: approved WhatsApp Templates as Frappe CRM's template picker reads them."""

	def load_from_db(self):
		"""
		Load one template by name.

		Returns:
		        None
		"""
		super(Document, self).__init__(load_template(self.name))

	def db_insert(self, *args, **kwargs):
		"""
		Refuse: templates are made in WhatsApp Template.

		Returns:
		        None
		"""
		frappe.throw(_("Create templates in WhatsApp Template"))

	def db_update(self, *args, **kwargs):
		"""
		Refuse: templates are changed in WhatsApp Template.

		Returns:
		        None
		"""
		frappe.throw(_("Change templates in WhatsApp Template"))

	def delete(self, *args, **kwargs):
		"""
		Refuse: templates are deleted in WhatsApp Template.

		Returns:
		        None
		"""
		frappe.throw(_("Delete templates in WhatsApp Template"))

	@staticmethod
	def get_list(args=None, **kwargs):
		"""
		Return the approved templates (Frappe 15 passes args, Frappe 16 keyword arguments).

		Parameters:
		        args (dict, optional): The list arguments; only "fields" is used.

		Returns:
		        list[dict]: Template rows.
		"""
		return list_templates()

	@staticmethod
	def get_count(args=None, **kwargs):
		"""
		Return the number of approved templates.

		Returns:
		        int: The count.
		"""
		return count_templates()

	@staticmethod
	def get_stats(args=None, **kwargs):
		"""
		Return no sidebar statistics.

		Returns:
		        dict: Empty.
		"""
		return {}
