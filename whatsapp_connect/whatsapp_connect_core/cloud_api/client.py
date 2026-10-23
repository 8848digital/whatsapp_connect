# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Graph API client for one WhatsApp Account."""

import requests

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api.errors import CloudAPIError
from whatsapp_connect.whatsapp_connect_core.cloud_api.request_log import log_request

TIMEOUT_SECONDS = 30


class CloudAPI:
	"""Calls to the Graph API for one WhatsApp Account."""

	def __init__(self, account: "str | frappe.model.document.Document"):
		"""
		Load the account and its access token.

		Parameters:
		        account (str | Document, required): A WhatsApp Account name or document.

		Returns:
		        None
		"""
		self.account = (
			frappe.get_doc("WhatsApp Account", account) if isinstance(account, str) else account
		)
		self.token = self.account.get_password("access_token")
		self.base_url = f"{self.account.graph_api_url.rstrip('/')}/{self.account.graph_api_version}"

	def send_message(self, payload: dict) -> str:
		"""
		Send a message from this account's phone number.

		Parameters:
		        payload (dict, required): The message object without "messaging_product".

		Returns:
		        str: The WhatsApp message ID (wamid) that Meta assigned.
		"""
		body = {"messaging_product": "whatsapp", **payload}
		response = self.request("POST", f"{self.account.phone_number_id}/messages", json_body=body)
		return response["messages"][0]["id"]

	def mark_as_read(self, wamid: str) -> None:
		"""
		Mark an incoming message as read (blue ticks).

		Parameters:
		        wamid (str, required): The WhatsApp message ID of the incoming message.

		Returns:
		        None
		"""
		body = {"messaging_product": "whatsapp", "status": "read", "message_id": wamid}
		self.request("POST", f"{self.account.phone_number_id}/messages", json_body=body)

	def upload_media(self, content: bytes, filename: str, mime_type: str) -> str:
		"""
		Upload a file to Meta so that messages can refer to it by media ID.

		Parameters:
		        content (bytes, required): The file content.
		        filename (str, required): The file name shown to the customer.
		        mime_type (str, required): The MIME type, for example "application/pdf".

		Returns:
		        str: The media ID.
		"""
		response = self.request(
			"POST",
			f"{self.account.phone_number_id}/media",
			data={"messaging_product": "whatsapp", "type": mime_type},
			files={"file": (filename, content, mime_type)},
		)
		return response["id"]

	def get_media(self, media_id: str) -> dict:
		"""
		Get the temporary download URL and MIME type of a media file.

		Parameters:
		        media_id (str, required): The media ID from an incoming message.

		Returns:
		        dict: Meta's media object with "url" and "mime_type".
		"""
		return self.request("GET", media_id)

	def download(self, url: str) -> bytes:
		"""
		Download a media file from Meta's temporary URL.

		Parameters:
		        url (str, required): The URL returned by get_media.

		Returns:
		        bytes: The file content.
		"""
		response = requests.get(url, headers=self.headers, timeout=TIMEOUT_SECONDS)
		if not response.ok:
			raise CloudAPIError(_("Media download failed"), http_status=response.status_code)
		return response.content

	def subscribe_app(self) -> dict:
		"""
		Subscribe the Meta app to the WhatsApp Business Account, so webhooks arrive.

		Returns:
		        dict: Meta's response, {"success": true} when it worked.
		"""
		return self.request("POST", f"{self.account.business_account_id}/subscribed_apps")

	@property
	def headers(self) -> dict:
		"""
		Return the authorization header for the Graph API.

		Returns:
		        dict: {"Authorization": "Bearer <token>"}.
		"""
		return {"Authorization": f"Bearer {self.token}"}

	def request(
		self, method: str, path: str, json_body=None, data=None, files=None, params=None
	) -> dict:
		"""
		Call the Graph API, log the call, and raise CloudAPIError on an error answer.

		Parameters:
		        method (str, required): HTTP method.
		        path (str, required): Path after the API version, for example "<phone_id>/messages".
		        json_body (dict, optional): JSON body.
		        data (dict, optional): Form fields, for multipart uploads.
		        files (dict, optional): Files, for multipart uploads.
		        params (dict, optional): Query string parameters.

		Returns:
		        dict: The decoded JSON answer.
		"""
		url = f"{self.base_url}/{path.lstrip('/')}"
		try:
			response = requests.request(
				method,
				url,
				headers=self.headers,
				json=json_body,
				data=data,
				files=files,
				params=params,
				timeout=TIMEOUT_SECONDS,
			)
		except requests.RequestException as exc:
			log_request(self.account.name, method, path, json_body or data, None, None, str(exc))
			raise CloudAPIError(_("Could not reach the WhatsApp Cloud API"), details=str(exc)) from exc

		answer = self.__decode(response)
		error = answer.get("error") if isinstance(answer, dict) else None
		log_request(
			self.account.name,
			method,
			path,
			json_body or data,
			response.status_code,
			answer,
			error and error.get("message"),
		)
		if not response.ok or error:
			raise self.__to_error(error or {}, response.status_code)
		return answer

	def __decode(self, response) -> dict:
		"""
		Decode a JSON answer; keep the text when the answer is not JSON.

		Parameters:
		        response (requests.Response, required): The HTTP response.

		Returns:
		        dict: The JSON object, or {"raw": text}.
		"""
		try:
			return response.json()
		except ValueError:
			return {"raw": response.text}

	def __to_error(self, error: dict, http_status: int) -> CloudAPIError:
		"""
		Build a CloudAPIError from Meta's error object.

		Parameters:
		        error (dict, required): Meta's "error" object (may be empty).
		        http_status (int, required): HTTP status of the answer.

		Returns:
		        CloudAPIError: The error to raise.
		"""
		details = (error.get("error_data") or {}).get("details")
		message = error.get("error_user_msg") or error.get("message") or _("WhatsApp Cloud API error")
		return CloudAPIError(message, code=error.get("code"), details=details, http_status=http_status)
