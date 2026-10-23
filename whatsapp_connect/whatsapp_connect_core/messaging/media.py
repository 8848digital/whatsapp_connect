# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Media: upload attachments to Meta, and save media that customers send."""

import mimetypes
from urllib.parse import unquote, urlparse

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI

DEFAULT_MIME_TYPE = "application/octet-stream"


def get_media_object(
	api: CloudAPI, file_url: str, filename: str | None = None, kind: str = "document"
) -> dict:
	"""
	Return the media object for a message: an uploaded media ID, or a link.

	A file stored on this site is uploaded to Meta, so private files and sites
	that Meta cannot reach work. A file on another site is sent as a link.

	Parameters:
	        api (CloudAPI, required): Client of the sending account.
	        file_url (str, required): The attachment URL ("/files/...", "/private/files/..." or "https://...").
	        filename (str, optional): File name shown for documents; defaults to the stored name.
	        kind (str, optional): "image", "document", "video", "audio" or "sticker". Default "document".

	Returns:
	        dict: {"id": ...} or {"link": ...}, with "filename" for documents.
	"""
	file_doc = get_local_file(file_url)
	if file_doc:
		content = file_doc.get_content()
		if isinstance(content, str):
			# Frappe returns text files decoded; Meta needs the original bytes.
			content = content.encode()
		mime_type = mimetypes.guess_type(file_doc.file_name or "")[0] or DEFAULT_MIME_TYPE
		media = {"id": api.upload_media(content, file_doc.file_name, mime_type)}
		filename = filename or file_doc.file_name
	elif file_url.startswith(("http://", "https://")):
		media = {"link": file_url}
	else:
		frappe.throw(_("Attachment {0} was not found").format(file_url))

	if kind == "document" and filename:
		media["filename"] = filename
	return media


def get_local_file(file_url: str | None):
	"""
	Return the File document of an attachment stored on this site.

	Parameters:
	        file_url (str, optional): A relative or absolute file URL.

	Returns:
	        Document | None: The File, or None for files on other sites.
	"""
	if not file_url:
		return None
	path = file_url
	site_url = frappe.utils.get_url()
	if path.startswith(site_url):
		path = path[len(site_url) :]
	elif path.startswith(("http://", "https://")):
		return None

	path = unquote(urlparse(path).path)
	name = frappe.db.get_value("File", {"file_url": path if path.startswith("/") else f"/{path}"})
	return frappe.get_doc("File", name) if name else None


def save_incoming_media(message_name: str) -> None:
	"""
	Download the media of an incoming message from Meta and attach it as a private file.

	Runs as a background job, so the webhook answers Meta quickly.

	Parameters:
	        message_name (str, required): The WhatsApp Message name.

	Returns:
	        None
	"""
	message = frappe.get_doc("WhatsApp Message", message_name)
	if not message.media_id or message.attachment:
		return

	api = CloudAPI(message.whatsapp_account)
	media = api.get_media(message.media_id)
	content = api.download(media["url"])
	mime_type = media.get("mime_type") or message.mime_type or DEFAULT_MIME_TYPE
	extension = mimetypes.guess_extension(mime_type.split(";")[0]) or ""
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": message.filename or f"{message.media_id}{extension}",
			"content": content,
			"is_private": 1,
			"attached_to_doctype": "WhatsApp Message",
			"attached_to_name": message.name,
			"attached_to_field": "attachment",
		}
	).insert(ignore_permissions=True)
	message.db_set({"attachment": file_doc.file_url, "mime_type": mime_type})
