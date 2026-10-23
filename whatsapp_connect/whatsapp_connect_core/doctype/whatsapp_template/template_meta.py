# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Keep WhatsApp Templates in step with Meta: submit, sync, delete and status updates."""

import mimetypes

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI, CloudAPIError
from whatsapp_connect.whatsapp_connect_core.cloud_api import templates as template_api
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_template.template_utils import (
	MEDIA_HEADERS,
	META_BUTTON_TYPES,
	build_components,
)
from whatsapp_connect.whatsapp_connect_core.messaging.media import get_local_file

META_STATUSES = {
	"APPROVED": "Approved",
	"PENDING": "Pending",
	"REJECTED": "Rejected",
	"PAUSED": "Paused",
	"DISABLED": "Disabled",
	"IN_APPEAL": "In Appeal",
	"PENDING_DELETION": "Deleted",
	"DELETED": "Deleted",
}
BUTTON_TYPES = {meta: local for local, meta in META_BUTTON_TYPES.items()}


def submit_template(template_name: str) -> str:
	"""
	Send the template to Meta: create it, or update it when Meta already has it.

	Parameters:
	        template_name (str, required): The WhatsApp Template name.

	Returns:
	        str: The template status after the call.
	"""
	template = frappe.get_doc("WhatsApp Template", template_name)
	template.check_permission("write")
	api = CloudAPI(template.whatsapp_account)
	definition = {
		"name": template.template_name,
		"language": template.language_code,
		"category": template.category,
		"components": build_components(template, __header_handle(api, template)),
	}
	if template.meta_template_id:
		template_api.update_template(api, template.meta_template_id, definition)
		status = "Pending"
	else:
		answer = template_api.create_template(api, definition)
		template.db_set("meta_template_id", answer.get("id"))
		status = META_STATUSES.get(answer.get("status"), "Pending")
	template.db_set({"status": status, "rejected_reason": None})
	return status


def sync_templates(account: str) -> int:
	"""
	Create or update local templates from all templates of an account in Meta.

	Parameters:
	        account (str, required): The WhatsApp Account name.

	Returns:
	        int: The number of templates synced.
	"""
	frappe.has_permission("WhatsApp Template", "write", throw=True)
	meta_templates = template_api.list_templates(CloudAPI(account))
	for meta_template in meta_templates:
		__save_from_meta(meta_template, account)
	return len(meta_templates)


def delete_in_meta(template) -> None:
	"""
	Delete the template in Meta before it is deleted here (on_trash).

	When Meta refuses (template already gone, expired token), the local delete
	still goes on and Meta's reason is shown.

	Parameters:
	        template (Document, required): The WhatsApp Template being deleted.

	Returns:
	        None
	"""
	if not template.meta_template_id:
		return
	try:
		template_api.delete_template(
			CloudAPI(template.whatsapp_account), template.template_name, template.meta_template_id
		)
	except CloudAPIError as error:
		frappe.msgprint(
			_("Deleted here only. Meta did not delete the template: {0}").format(error.describe()),
			indicator="orange",
		)


def update_template_status(value: dict) -> None:
	"""
	Apply a message_template_status_update webhook event.

	Parameters:
	        value (dict, required): event, message_template_id and reason.

	Returns:
	        None
	"""
	name = frappe.db.get_value(
		"WhatsApp Template", {"meta_template_id": str(value.get("message_template_id"))}
	)
	if not name:
		return
	reason = value.get("reason")
	frappe.db.set_value(
		"WhatsApp Template",
		name,
		{
			"status": META_STATUSES.get(value.get("event"), "Pending"),
			"rejected_reason": None if reason in (None, "NONE") else reason,
		},
	)


def __header_handle(api: CloudAPI, template) -> str | None:
	"""
	Upload the sample file of a media header and return its handle.

	Parameters:
	        api (CloudAPI, required): Client of the account.
	        template (Document, required): The WhatsApp Template.

	Returns:
	        str | None: The handle, or None when the template has no media header.
	"""
	if template.header_type not in MEDIA_HEADERS:
		return None
	file_doc = get_local_file(template.header_sample_file)
	if not file_doc:
		frappe.throw(_("Attach a sample file for the {0} header").format(_(template.header_type)))
	content = file_doc.get_content()
	content = content.encode() if isinstance(content, str) else content
	mime_type = mimetypes.guess_type(file_doc.file_name)[0] or "application/octet-stream"
	return template_api.upload_sample(api, content, file_doc.file_name, mime_type)


def __save_from_meta(meta_template: dict, account: str) -> None:
	"""
	Create or update one local template from Meta's template object.

	Parameters:
	        meta_template (dict, required): Meta's template object.
	        account (str, required): The WhatsApp Account name.

	Returns:
	        None
	"""
	name = frappe.db.get_value(
		"WhatsApp Template", {"meta_template_id": meta_template["id"]}
	) or frappe.db.get_value(
		"WhatsApp Template",
		{"template_name": meta_template["name"], "language_code": meta_template["language"]},
	)
	template = (
		frappe.get_doc("WhatsApp Template", name) if name else frappe.new_doc("WhatsApp Template")
	)
	template.update(
		{
			"template_name": meta_template["name"],
			"language_code": meta_template["language"],
			"category": meta_template.get("category") or "UTILITY",
			"whatsapp_account": account,
			"meta_template_id": meta_template["id"],
			"status": META_STATUSES.get(meta_template.get("status"), "Pending"),
			"rejected_reason": None
			if meta_template.get("rejected_reason") in (None, "NONE")
			else meta_template["rejected_reason"],
		}
	)
	template.set("buttons", [])
	for component in meta_template.get("components") or []:
		__apply_component(template, component)
	template.flags.from_meta = True
	template.save(ignore_permissions=True)


def __apply_component(template, component: dict) -> None:
	"""
	Copy one Meta component (header, body, footer or buttons) onto the local template.

	Parameters:
	        template (Document, required): The WhatsApp Template being filled.
	        component (dict, required): Meta's component object.

	Returns:
	        None
	"""
	kind = component.get("type")
	example = component.get("example") or {}
	if kind == "HEADER":
		template.header_type = (component.get("format") or "").title()
		template.header_text = component.get("text")
		template.header_sample = (example.get("header_text") or [None])[0]
	elif kind == "BODY":
		template.body = component.get("text") or template.body or ""
		template.body_samples = "\n".join((example.get("body_text") or [[]])[0])
	elif kind == "FOOTER":
		template.footer = component.get("text")
	elif kind == "BUTTONS":
		for button in component.get("buttons") or []:
			template.append(
				"buttons",
				{
					"button_type": BUTTON_TYPES.get(button.get("type"), "Quick Reply"),
					"label": button.get("text"),
					"phone_number": button.get("phone_number"),
					"url": button.get("url"),
					"url_sample": (button.get("example") or [None])[0]
					if isinstance(button.get("example"), list)
					else None,
					"code_sample": button.get("example") if isinstance(button.get("example"), str) else None,
					"flow_id": button.get("flow_id"),
					"flow_screen": button.get("navigate_screen"),
				},
			)
