# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Keep WhatsApp Flows in step with Meta: save, publish, deprecate, delete, status and import."""

import json

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI, CloudAPIError
from whatsapp_connect.whatsapp_connect_flow import flow_api

ENDPOINT_PATH = "/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.endpoint.receive"
META_STATUSES = {
	"DRAFT": "Draft",
	"PUBLISHED": "Published",
	"DEPRECATED": "Deprecated",
	"BLOCKED": "Blocked",
	"THROTTLED": "Throttled",
}


def save_to_meta(flow_name: str) -> list:
	"""
	Create the flow in Meta (or update it) and upload its Flow JSON.

	Parameters:
	        flow_name (str, required): The WhatsApp Flow name.

	Returns:
	        list: Meta's validation errors of the JSON; empty when it is valid.
	"""
	flow = __load(flow_name, "write", require_meta_id=False)
	if not flow.flow_json:
		frappe.throw(_("Add screens and components, or write the Flow JSON, first"))
	api = CloudAPI(flow.whatsapp_account)
	endpoint = frappe.utils.get_url(ENDPOINT_PATH) if flow.use_endpoint else None
	if flow.meta_flow_id:
		flow_api.update_flow(api, flow.meta_flow_id, flow.flow_name, [flow.category], endpoint)
	else:
		flow.db_set("meta_flow_id", flow_api.create_flow(api, flow.flow_name, [flow.category], endpoint))
	errors = flow_api.upload_flow_json(api, flow.meta_flow_id, flow.flow_json)
	flow.db_set("validation_errors", __describe(errors) or None)
	refresh_status(flow_name)
	return errors


def publish(flow_name: str) -> str:
	"""
	Publish the flow in Meta; after that it cannot be changed.

	Parameters:
	        flow_name (str, required): The WhatsApp Flow name.

	Returns:
	        str: The new status.
	"""
	return __action(flow_name, "publish")


def deprecate(flow_name: str) -> str:
	"""
	Deprecate a published flow, so it can no longer be sent.

	Parameters:
	        flow_name (str, required): The WhatsApp Flow name.

	Returns:
	        str: The new status.
	"""
	return __action(flow_name, "deprecate")


def refresh_status(flow_name: str) -> dict:
	"""
	Read the flow's status, validation errors and preview link from Meta.

	Parameters:
	        flow_name (str, required): The WhatsApp Flow name.

	Returns:
	        dict: Meta's flow object.
	"""
	flow = __load(flow_name, "read")
	meta_flow = flow_api.get_flow(CloudAPI(flow.whatsapp_account), flow.meta_flow_id)
	flow.db_set(
		{
			"status": META_STATUSES.get(meta_flow.get("status"), flow.status),
			"preview_url": (meta_flow.get("preview") or {}).get("preview_url"),
			"validation_errors": __describe(meta_flow.get("validation_errors")) or None,
		}
	)
	return meta_flow


def delete_in_meta(flow) -> None:
	"""
	Delete a draft flow in Meta before the local flow is deleted (on_trash).

	Published flows cannot be deleted in Meta; the local delete still goes on.

	Parameters:
	        flow (Document, required): The WhatsApp Flow being deleted.

	Returns:
	        None
	"""
	if not flow.meta_flow_id or flow.status != "Draft":
		return
	try:
		flow_api.delete_flow(CloudAPI(flow.whatsapp_account), flow.meta_flow_id)
	except CloudAPIError as error:
		frappe.msgprint(
			_("Deleted here only. Meta did not delete the flow: {0}").format(error.describe()),
			indicator="orange",
		)


def import_flows(account: str) -> int:
	"""
	Create or update local flows from the account's flows in Meta, with their Flow JSON.

	Imported flows keep the JSON as written in Meta (Edit Flow JSON Directly).

	Parameters:
	        account (str, required): The WhatsApp Account name.

	Returns:
	        int: The number of flows imported.
	"""
	frappe.has_permission("WhatsApp Flow", "write", throw=True)
	api = CloudAPI(account)
	meta_flows = flow_api.list_flows(api)
	for meta_flow in meta_flows:
		name = frappe.db.get_value("WhatsApp Flow", {"meta_flow_id": meta_flow["id"]})
		flow = frappe.get_doc("WhatsApp Flow", name) if name else frappe.new_doc("WhatsApp Flow")
		flow.update(
			{
				"flow_name": flow.flow_name or meta_flow["name"],
				"whatsapp_account": account,
				"meta_flow_id": meta_flow["id"],
				"category": (meta_flow.get("categories") or ["OTHER"])[0],
				"status": META_STATUSES.get(meta_flow.get("status"), "Draft"),
				"edit_json": 1,
				"flow_json": flow_api.download_flow_json(api, meta_flow["id"])
				or json.dumps({"version": "6.0", "screens": []}),
			}
		)
		flow.flags.from_meta = True
		flow.save(ignore_permissions=True)
	return len(meta_flows)


def __action(flow_name: str, action: str) -> str:
	"""
	Run publish or deprecate in Meta and read the new status.

	Parameters:
	        flow_name (str, required): The WhatsApp Flow name.
	        action (str, required): "publish" or "deprecate".

	Returns:
	        str: The new status.
	"""
	flow = __load(flow_name, "write")
	flow_api.flow_action(CloudAPI(flow.whatsapp_account), flow.meta_flow_id, action)
	refresh_status(flow_name)
	return frappe.db.get_value("WhatsApp Flow", flow_name, "status")


def __load(flow_name: str, permission: str, require_meta_id: bool = True):
	"""
	Load a flow and check the user's permission; actions other than save need a Meta ID.

	Parameters:
	        flow_name (str, required): The WhatsApp Flow name.
	        permission (str, required): "read" or "write".
	        require_meta_id (bool, optional): Refuse flows that Meta does not have yet. Default True.

	Returns:
	        Document: The WhatsApp Flow.
	"""
	flow = frappe.get_doc("WhatsApp Flow", flow_name)
	flow.check_permission(permission)
	if require_meta_id and not flow.meta_flow_id:
		frappe.throw(_("Save the flow to Meta first"))
	return flow


def __describe(errors) -> str:
	"""
	Turn Meta's validation errors into readable lines.

	Parameters:
	        errors (list, optional): Meta's validation error objects.

	Returns:
	        str: One line per error.
	"""
	lines = []
	for error in errors or []:
		where = " ".join(str(error.get(key)) for key in ("pointers", "line_start") if error.get(key))
		lines.append(
			f"{error.get('error_type') or error.get('error')}: {error.get('message')} {where}".strip()
		)
	return "\n".join(lines)
