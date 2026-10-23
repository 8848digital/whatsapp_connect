# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Hub page that runs Meta's Embedded Signup for a site's signup session."""

from urllib.parse import urlparse

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	"""
	Load the hub's Meta app settings and the site of the signup session.

	Parameters:
	        context (dict, required): The page context.

	Returns:
	        dict: The context with app_id, config_id, graph_api_version, session,
	                site_origin, coexistence, or an error text.
	"""
	settings = frappe.get_cached_doc("WhatsApp Hub Settings")
	if not settings.enabled:
		raise frappe.PageDoesNotExistError
	session = frappe.form_dict.get("session") or ""
	connection = frappe.db.get_value(
		"WhatsApp Hub Connection",
		{"name": session, "status": "Pending"},
		["site_url", "coexistence"],
		as_dict=True,
	)
	context.title = _("Connect WhatsApp")
	context.no_breadcrumbs = 1
	if not connection:
		context.error = _("This signup link is not valid or has expired. Start again from your site.")
		return context
	site = urlparse(connection.site_url)
	context.update(
		{
			"app_id": settings.app_id,
			"config_id": settings.config_id,
			"graph_api_version": settings.graph_api_version,
			"session": session,
			"site_origin": f"{site.scheme}://{site.netloc}",
			"site_host": site.netloc,
			"coexistence": int(connection.coexistence or 0),
		}
	)
	return context
