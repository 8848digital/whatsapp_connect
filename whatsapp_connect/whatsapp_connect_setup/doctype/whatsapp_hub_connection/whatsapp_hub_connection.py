# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document


class WhatsAppHubConnection(Document):
	"""A site that connected WhatsApp through this hub; the hub forwards its webhooks."""
