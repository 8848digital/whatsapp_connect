# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Graph API calls for WhatsApp Flows."""

import json

import requests

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI, CloudAPIError
from whatsapp_connect.whatsapp_connect_core.cloud_api.client import TIMEOUT_SECONDS

FLOW_FIELDS = "id,name,status,categories,validation_errors,preview"


def create_flow(
	api: CloudAPI, name: str, categories: list[str], endpoint_uri: str | None = None
) -> str:
	"""
	Create a draft flow in the WhatsApp Business Account.

	Parameters:
	        api (CloudAPI, required): Client of the account.
	        name (str, required): Flow name.
	        categories (list[str], required): Meta categories, for example ["LEAD_GENERATION"].
	        endpoint_uri (str, optional): Data endpoint URL for flows that use one.

	Returns:
	        str: Meta's flow ID.
	"""
	body = {"name": name, "categories": categories}
	if endpoint_uri:
		body["endpoint_uri"] = endpoint_uri
	return api.request("POST", f"{api.account.business_account_id}/flows", json_body=body)["id"]


def update_flow(
	api: CloudAPI, flow_id: str, name: str, categories: list[str], endpoint_uri: str | None = None
) -> dict:
	"""
	Change the name, categories and endpoint of a flow.

	Parameters:
	        api (CloudAPI, required): Client of the account.
	        flow_id (str, required): Meta's flow ID.
	        name (str, required): Flow name.
	        categories (list[str], required): Meta categories.
	        endpoint_uri (str, optional): Data endpoint URL.

	Returns:
	        dict: Meta's answer.
	"""
	body = {"name": name, "categories": categories}
	if endpoint_uri:
		body["endpoint_uri"] = endpoint_uri
	return api.request("POST", flow_id, json_body=body)


def upload_flow_json(api: CloudAPI, flow_id: str, flow_json: str) -> list:
	"""
	Upload the Flow JSON as the flow's asset; Meta answers with validation errors, if any.

	Parameters:
	        api (CloudAPI, required): Client of the account.
	        flow_id (str, required): Meta's flow ID.
	        flow_json (str, required): The Flow JSON text.

	Returns:
	        list: Meta's validation errors (empty when the JSON is valid).
	"""
	answer = api.request(
		"POST",
		f"{flow_id}/assets",
		data={"name": "flow.json", "asset_type": "FLOW_JSON"},
		files={"file": ("flow.json", flow_json.encode(), "application/json")},
	)
	return answer.get("validation_errors") or []


def flow_action(api: CloudAPI, flow_id: str, action: str) -> dict:
	"""
	Publish or deprecate a flow.

	Parameters:
	        api (CloudAPI, required): Client of the account.
	        flow_id (str, required): Meta's flow ID.
	        action (str, required): "publish" or "deprecate".

	Returns:
	        dict: Meta's answer.
	"""
	return api.request("POST", f"{flow_id}/{action}")


def delete_flow(api: CloudAPI, flow_id: str) -> dict:
	"""
	Delete a draft flow in Meta.

	Parameters:
	        api (CloudAPI, required): Client of the account.
	        flow_id (str, required): Meta's flow ID.

	Returns:
	        dict: Meta's answer.
	"""
	return api.request("DELETE", flow_id)


def get_flow(api: CloudAPI, flow_id: str) -> dict:
	"""
	Read a flow's status, validation errors and preview link.

	Parameters:
	        api (CloudAPI, required): Client of the account.
	        flow_id (str, required): Meta's flow ID.

	Returns:
	        dict: Meta's flow object.
	"""
	return api.request("GET", flow_id, params={"fields": FLOW_FIELDS})


def list_flows(api: CloudAPI) -> list[dict]:
	"""
	Return the flows of the account's WhatsApp Business Account.

	Parameters:
	        api (CloudAPI, required): Client of the account.

	Returns:
	        list[dict]: Meta's flow objects.
	"""
	return (
		api.request(
			"GET",
			f"{api.account.business_account_id}/flows",
			params={"fields": "id,name,status,categories"},
		).get("data")
		or []
	)


def download_flow_json(api: CloudAPI, flow_id: str) -> str | None:
	"""
	Download the Flow JSON asset of a flow.

	Parameters:
	        api (CloudAPI, required): Client of the account.
	        flow_id (str, required): Meta's flow ID.

	Returns:
	        str | None: The Flow JSON text, or None when the flow has no JSON asset.
	"""
	assets = api.request("GET", f"{flow_id}/assets").get("data") or []
	asset = next((item for item in assets if item.get("asset_type") == "FLOW_JSON"), None)
	if not asset:
		return None
	response = requests.get(asset["download_url"], timeout=TIMEOUT_SECONDS)
	if not response.ok:
		raise CloudAPIError("Flow JSON download failed", http_status=response.status_code)
	return json.dumps(response.json(), indent=2)


def upload_public_key(api: CloudAPI, public_key_pem: str) -> dict:
	"""
	Register the business public key that Meta uses to encrypt Flow endpoint calls.

	Parameters:
	        api (CloudAPI, required): Client of the account (the key is set per phone number).
	        public_key_pem (str, required): The RSA public key in PEM format.

	Returns:
	        dict: Meta's answer.
	"""
	return api.request(
		"POST",
		f"{api.account.phone_number_id}/whatsapp_business_encryption",
		data={"business_public_key": public_key_pem},
	)
