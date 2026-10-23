# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""The text of a template with its variables filled, for previews."""

import frappe

from whatsapp_connect.whatsapp_connect_core.messaging.template_params import get_template_params


def render_preview(
	template_name: str, doctype: str | None = None, name: str | None = None
) -> dict:
	"""
	Fill the template's variables from a document (or the samples) for display.

	Parameters:
	        template_name (str, required): The WhatsApp Template name.
	        doctype (str, optional): Doctype of the document.
	        name (str, optional): Name of the document.

	Returns:
	        dict: header, header_type, body, footer and button labels.
	"""
	template = frappe.get_doc("WhatsApp Template", template_name)
	template.check_permission("read")
	doc = None
	if doctype and name:
		doc = frappe.get_doc(doctype, name)
		doc.check_permission("read")
	params = get_template_params(template, doc)

	body = template.body or ""
	for index, value in enumerate(params["body"], start=1):
		body = body.replace("{{%d}}" % index, value)
	header = template.header_text or ""
	if params["header"]:
		header = header.replace("{{1}}", params["header"][0])
	return {
		"header": header,
		"header_type": template.header_type,
		"body": body,
		"footer": template.footer,
		"buttons": [button.label for button in template.buttons if button.label],
	}
