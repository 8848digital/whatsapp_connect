# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Install hooks of WhatsApp Connect."""

import frappe

ROLES = ("WhatsApp Manager", "WhatsApp User")


def before_install() -> None:
	"""
	Create the app's roles, which the DocType permissions refer to.

	Returns:
	        None
	"""
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)
