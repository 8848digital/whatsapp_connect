# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""
Custom `8848-export-fixtures` bench command.

Location: apps/<app_name>/<app_name>/commands/export_fixtures.py
This is a copy-pasteable template — see project_base_template/commands/README.md
for the full setup steps and CLAUDE.md's `commands/` directory entry for where
it fits in the app structure. Reads fixture definitions from the app's own
`custom_fixtures` hook (not Frappe's built-in `fixtures` hook) and strips
null/empty/zero-valued fields before writing, keeping fixture JSON small and
diff-friendly. Registered via `commands = [...]` in this package's
`__init__.py`, then wired into `hooks.py`'s `commands` list — see
bench-operations.md.
"""

import os

import click
import frappe
from frappe.commands import pass_context
from frappe.exceptions import SiteNotSpecifiedError


@click.command("8848-export-fixtures")
@click.option("--app", default=None, help="Export fixtures of a specific app")
@pass_context
def export_fixtures(context, app=None):
	"""
	Bench command entry point: `bench --site <site> 8848-export-fixtures [--app <app_name>]`.

	Parameters:
		context (click.Context, required): Bench's click context, carrying `context.sites`.
		app (str, optional): Restrict export to a single installed app. Defaults to
			exporting for every installed app.

	Returns:
		None
	"""
	for site in context.sites:
		try:
			frappe.init(site=site)
			frappe.connect()
			__export_fixtures(app=app)
		finally:
			frappe.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError


def __export_fixtures(app=None):
	"""
	Export every fixture listed in the `custom_fixtures` hook to `[app]/fixtures/`.

	Parameters:
		app (str, optional): Restrict export to this installed app. Defaults to
			every installed app.

	Returns:
		None
	"""
	apps = [app] if app else frappe.get_installed_apps()
	for app in apps:
		for fixture in frappe.get_hooks("custom_fixtures", app_name=app):
			filters = None
			or_filters = None
			if isinstance(fixture, dict):
				filters = fixture.get("filters")
				or_filters = fixture.get("or_filters")
				fixture = fixture.get("doctype") or fixture.get("dt")
			print(
				f"Exporting {fixture} app {app} filters {(filters if filters else or_filters)}"
			)
			if not os.path.exists(frappe.get_app_path(app, "fixtures")):
				os.mkdir(frappe.get_app_path(app, "fixtures"))

			__export_json(
				fixture,
				frappe.get_app_path(app, "fixtures", frappe.scrub(fixture) + ".json"),
				filters=filters,
				or_filters=or_filters,
				order_by="idx asc, creation asc",
			)


def __export_json(
	doctype, path, filters=None, or_filters=None, name=None, order_by="creation asc"
):
	"""
	Fetch matching documents for `doctype` and write them to `path` as fixture JSON,
	with empty/null fields and internal bookkeeping fields (creation, owner, lft/rgt,
	etc.) stripped out.

	Parameters:
		doctype (str, required): DocType to export.
		path (str, required): Destination JSON file path.
		filters (dict, optional): Passed through to `frappe.get_all`.
		or_filters (dict, optional): Passed through to `frappe.get_all`.
		name (str, optional): Export exactly this one document instead of querying.
		order_by (str, optional): Passed through to `frappe.get_all`. Default `"creation asc"`.

	Returns:
		None
	"""

	def post_process(out):
		# Note on Tree DocTypes:
		# The tree structure is maintained in the database via the fields "lft"
		# and "rgt". They are automatically set and kept up-to-date. Importing
		# them would destroy any existing tree structure. For this reason they
		# are not exported as well.
		del_keys = ("modified_by", "creation", "owner", "idx", "lft", "rgt")
		for doc in out:
			# Custom Fixtures: Remove keys that are not needed in the fixture
			for key in list(doc.keys()):
				if not doc.get(key):
					del doc[key]  # Remove keys with null, "" or 0 values

			for key in del_keys:
				if key in doc:
					del doc[key]

			for v in doc.values():
				if isinstance(v, list):
					for child in v:
						# Custom Fixtures: Remove keys that are not needed in the fixture from child
						for key in list(child.keys()):
							if not child.get(key):
								del child[key]  # Remove keys with null, "" or 0 values from child

						for key in (
							*del_keys,
							"docstatus",
							"doctype",
							"modified",
							"name",
						):
							if key in child:
								del child[key]

	out = []
	if name:
		out.append(frappe.get_doc(doctype, name).as_dict())
	elif frappe.db.get_value("DocType", doctype, "issingle"):
		out.append(frappe.get_doc(doctype).as_dict())
	else:
		for doc in frappe.get_all(
			doctype,
			fields=["name"],
			filters=filters,
			or_filters=or_filters,
			limit_page_length=0,
			order_by=order_by,
		):
			out.append(frappe.get_doc(doctype, doc.name).as_dict())
	post_process(out)

	# Custom Fixtures: Custom Fields are exported to separate files based on their doctype (dt)
	if doctype == "Custom Field":
		dt_map = {}
		for row in out:
			dt_map.setdefault(row.dt, [])
			dt_map[row.dt].append(row)

		for dt, rows in dt_map.items():
			dt_path = path.replace("custom_field.json", f"{frappe.scrub(dt)}.json")
			dirname = os.path.dirname(dt_path)
			if not os.path.exists(dirname):
				dt_path = os.path.join("..", dt_path)

			with open(dt_path, "w") as outfile:
				outfile.write(frappe.as_json(rows, ensure_ascii=False))
	else:
		dirname = os.path.dirname(path)
		if not os.path.exists(dirname):
			path = os.path.join("..", path)

		with open(path, "w") as outfile:
			outfile.write(frappe.as_json(out, ensure_ascii=False))
