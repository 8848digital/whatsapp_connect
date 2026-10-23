# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from whatsapp_connect.whatsapp_connect_notification.doctype.whatsapp_notification.notification_utils import (
	clear_notification_map,
	validate_notification,
)


class WhatsAppNotification(Document):
	"""Sends a template automatically on a document event, a date or a schedule."""

	def validate(self):
		"""
		Check the trigger, fields, recipients and attachment settings.

		Returns:
		        None
		"""
		validate_notification(self)

	def on_update(self):
		"""
		Apply the change at once: the event map is cached.

		Returns:
		        None
		"""
		clear_notification_map()

	def on_trash(self):
		"""
		Remove the notification from the cached event map.

		Returns:
		        None
		"""
		clear_notification_map()
