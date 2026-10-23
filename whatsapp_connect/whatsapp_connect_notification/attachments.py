# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Header files for notification templates: the document print, a field's file, or a fixed file."""

import frappe


def get_header_media(notification, doc=None) -> dict:
	"""
	Return the header file values for the template, if the notification sets one.

	Parameters:
	        notification (Document, required): The WhatsApp Notification.
	        doc (Document, optional): The document.

	Returns:
	        dict: {"header_media": url, "header_filename": name}, or {} when no file is set.
	"""
	if notification.attach_print and doc is not None:
		file_doc = print_as_file(doc, notification.print_format)
		return {"header_media": file_doc.file_url, "header_filename": file_doc.file_name}
	if notification.attach_from_field and doc is not None and doc.get(notification.attach_from_field):
		return {"header_media": doc.get(notification.attach_from_field)}
	if notification.attach_file:
		return {"header_media": notification.attach_file}
	return {}


def print_as_file(doc, print_format: str | None = None):
	"""
	Render the document's print as a PDF and save it as a private file on the document.

	The file is then uploaded to Meta, so it reaches the customer even when Meta
	cannot open this site.

	Parameters:
	        doc (Document, required): The document to print.
	        print_format (str, optional): Print format; default: the doctype's default.

	Returns:
	        Document: The new File.
	"""
	print_format = print_format or frappe.get_meta(doc.doctype).default_print_format or "Standard"
	content = frappe.get_print(doc.doctype, doc.name, print_format, doc=doc, as_pdf=True)
	return frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{doc.name}.pdf".replace("/", "-"),
			"content": content,
			"is_private": 1,
			"attached_to_doctype": doc.doctype,
			"attached_to_name": doc.name,
		}
	).insert(ignore_permissions=True)
