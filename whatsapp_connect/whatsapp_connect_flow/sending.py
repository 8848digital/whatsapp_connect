# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Send a WhatsApp Flow as an interactive message."""

import json

import frappe
from frappe import _

FLOW_MESSAGE_VERSION = "3"


def build_flow_object(message, api) -> dict:
	"""
	Build the "interactive" object of a flow message (payload builder for message_type "flow").

	The message's payload holds {"flow", "flow_token", "screen"}. A draft flow is
	sent in Meta's draft mode, which works only for the account's test numbers.

	Parameters:
	        message (Document, required): The outgoing WhatsApp Message.
	        api (CloudAPI, required): Unused; part of the builder signature.

	Returns:
	        dict: The interactive flow object (core sends it with type "interactive").
	"""
	payload = json.loads(message.payload or "{}")
	flow = frappe.get_doc("WhatsApp Flow", payload.get("flow"))
	if not flow.meta_flow_id:
		frappe.throw(_("Flow {0} is not saved to Meta").format(flow.name))
	parameters = {
		"flow_message_version": FLOW_MESSAGE_VERSION,
		"flow_token": payload.get("flow_token"),
		"flow_id": flow.meta_flow_id,
		"flow_cta": flow.cta or _("Open"),
		"flow_action": "data_exchange" if flow.use_endpoint else "navigate",
	}
	if not flow.use_endpoint:
		first_screen = payload.get("screen") or (flow.screens[0].screen_id if flow.screens else None)
		parameters["flow_action_payload"] = {"screen": first_screen}
	if flow.status == "Draft":
		parameters["mode"] = "draft"
	return {
		"type": "flow",
		"body": {"text": message.body or flow.flow_name},
		"action": {"name": "flow", "parameters": parameters},
	}


def send_flow(flow: str, to: str, text: str | None = None, doc=None):
	"""
	Send a flow to a number.

	Parameters:
	        flow (str, required): The WhatsApp Flow name.
	        to (str, required): The recipient's number.
	        text (str, optional): Message text above the button; default: the flow name.
	        doc (Document, optional): The document the flow is sent from (linked to the message).

	Returns:
	        Document: The WhatsApp Message.
	"""
	settings = frappe.get_doc("WhatsApp Flow", flow)
	message = frappe.get_doc(
		{
			"doctype": "WhatsApp Message",
			"direction": "Outgoing",
			"message_type": "flow",
			"phone_number": to,
			"body": text or settings.flow_name,
			"whatsapp_account": settings.whatsapp_account,
			"payload": json.dumps({"flow": flow, "flow_token": frappe.generate_hash(length=20)}),
			"reference_doctype": doc.doctype if doc else None,
			"reference_name": doc.name if doc else None,
			"source": f"Flow: {flow}",
		}
	)
	message.insert(ignore_permissions=True)
	message.reload()
	return message
