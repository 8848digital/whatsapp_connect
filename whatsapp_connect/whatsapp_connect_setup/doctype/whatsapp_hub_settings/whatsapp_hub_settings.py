# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from frappe.model.document import Document


class WhatsAppHubSettings(Document):
	"""The Meta app of the 8848 hub, which runs Embedded Signup for other sites."""

	def validate(self):
		"""
		Clean the Graph API URL and version.

		Returns:
		        None
		"""
		self.graph_api_url = (self.graph_api_url or "https://graph.facebook.com").strip().rstrip("/")
		version = (self.graph_api_version or "v24.0").strip()
		self.graph_api_version = version if version.startswith("v") else f"v{version}"
