# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Let Frappe CRM's sales roles read the template list (after_migrate hook)."""

import frappe
from frappe.permissions import add_permission

SALES_ROLES = ("Sales Manager", "Sales User")


def add_crm_permissions() -> None:
	"""
	Give the sales roles read access to WhatsApp Templates when Frappe CRM is installed.

	Run "bench migrate" after installing Frappe CRM, so this hook runs.

	Returns:
	        None
	"""
	if "crm" not in frappe.get_installed_apps():
		return
	for role in SALES_ROLES:
		if frappe.db.exists("Role", role) and not frappe.db.exists(
			"Custom DocPerm", {"parent": "WhatsApp Templates", "role": role}
		):
			add_permission("WhatsApp Templates", role, 0, "read")
