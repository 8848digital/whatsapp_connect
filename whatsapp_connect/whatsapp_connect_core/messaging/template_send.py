# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Send a template from code; used by notifications, campaigns and the Send WhatsApp dialog."""

import json

import frappe


def send_template(
	template: str,
	to: str,
	doc=None,
	values: dict | None = None,
	account: str | None = None,
	source: str | None = None,
	skip_send: bool = False,
):
	"""
	Create (and send) a template message.

	Parameters:
	        template (str, required): The WhatsApp Template name.
	        to (str, required): The recipient's phone number in any format.
	        doc (Document, optional): The document the message is about; its fields fill
	                the variables and the message is linked to it.
	        values (dict, optional): Variable values that override the document fields.
	        account (str, optional): Sending WhatsApp Account; defaults to the template's account.
	        source (str, optional): What sends the message, for example "Notification: X".
	        skip_send (bool, optional): Save the message without sending it.

	Returns:
	        Document: The inserted WhatsApp Message (status Sent, Failed or Opted Out).
	"""
	template_account = frappe.db.get_value("WhatsApp Template", template, "whatsapp_account")
	message = frappe.get_doc(
		{
			"doctype": "WhatsApp Message",
			"direction": "Outgoing",
			"message_type": "template",
			"template": template,
			"template_params": json.dumps(values) if values else None,
			"phone_number": to,
			"whatsapp_account": account or template_account,
			"reference_doctype": doc.doctype if doc else None,
			"reference_name": doc.name if doc else None,
			"source": source,
		}
	)
	message.flags.skip_send = skip_send
	message.insert(ignore_permissions=True)
	message.reload()
	return message
