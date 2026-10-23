# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Graph API calls for message templates (WhatsApp Business Account level)."""

import requests

from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api.client import TIMEOUT_SECONDS, CloudAPI
from whatsapp_connect.whatsapp_connect_core.cloud_api.errors import CloudAPIError

TEMPLATE_FIELDS = "id,name,language,status,category,components,rejected_reason"
PAGE_SIZE = 100


def create_template(api: CloudAPI, definition: dict) -> dict:
	"""
	Submit a new template to Meta for approval.

	Parameters:
	        api (CloudAPI, required): Client of the account that owns the template.
	        definition (dict, required): name, language, category and components.

	Returns:
	        dict: Meta's answer with "id", "status" and "category".
	"""
	return api.request(
		"POST", f"{api.account.business_account_id}/message_templates", json_body=definition
	)


def update_template(api: CloudAPI, template_id: str, definition: dict) -> dict:
	"""
	Change the components (and category) of a template that Meta already has.

	Parameters:
	        api (CloudAPI, required): Client of the owning account.
	        template_id (str, required): Meta's template ID.
	        definition (dict, required): The new components, and the category.

	Returns:
	        dict: Meta's answer, {"success": true} when it worked.
	"""
	body = {key: definition[key] for key in ("components", "category") if key in definition}
	return api.request("POST", template_id, json_body=body)


def list_templates(api: CloudAPI) -> list[dict]:
	"""
	Return all templates of the account's WhatsApp Business Account, following pagination.

	Parameters:
	        api (CloudAPI, required): Client of the account.

	Returns:
	        list[dict]: Meta's template objects.
	"""
	templates = []
	path = f"{api.account.business_account_id}/message_templates"
	params = {"fields": TEMPLATE_FIELDS, "limit": PAGE_SIZE}
	while path:
		page = api.request("GET", path, params=params)
		templates.extend(page.get("data") or [])
		after = ((page.get("paging") or {}).get("cursors") or {}).get("after")
		path = path if after and (page.get("paging") or {}).get("next") else None
		params = {**params, "after": after}
	return templates


def delete_template(api: CloudAPI, name: str, template_id: str | None = None) -> dict:
	"""
	Delete a template in Meta (one language when the ID is given, else all languages).

	Parameters:
	        api (CloudAPI, required): Client of the owning account.
	        name (str, required): The template name.
	        template_id (str, optional): Meta's ID of one language version.

	Returns:
	        dict: Meta's answer.
	"""
	params = {"name": name}
	if template_id:
		params["hsm_id"] = template_id
	return api.request(
		"DELETE", f"{api.account.business_account_id}/message_templates", params=params
	)


def upload_sample(api: CloudAPI, content: bytes, filename: str, mime_type: str) -> str:
	"""
	Upload a sample header file with the Resumable Upload API and return its handle.

	Templates with an image, document or video header need such a handle for approval.

	Parameters:
	        api (CloudAPI, required): Client of the account; the account needs an App ID.
	        content (bytes, required): The file content.
	        filename (str, required): The file name.
	        mime_type (str, required): The MIME type.

	Returns:
	        str: The file handle ("h") for the template's header example.
	"""
	if not api.account.app_id:
		raise CloudAPIError(_("Set the App ID on the WhatsApp Account to upload header samples"))
	session = api.request(
		"POST",
		f"{api.account.app_id}/uploads",
		params={"file_name": filename, "file_length": len(content), "file_type": mime_type},
	)
	response = requests.post(
		f"{api.base_url}/{session['id']}",
		headers={"Authorization": f"OAuth {api.token}", "file_offset": "0"},
		data=content,
		timeout=TIMEOUT_SECONDS,
	)
	answer = response.json() if response.content else {}
	if not response.ok or not answer.get("h"):
		raise CloudAPIError(
			_("Header sample upload failed: {0}").format(response.text), http_status=response.status_code
		)
	return answer["h"]
