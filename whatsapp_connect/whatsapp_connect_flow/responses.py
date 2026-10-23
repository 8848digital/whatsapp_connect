# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Save Flow answers that arrive as incoming messages (whatsapp_connect_incoming_handlers hook)."""

import json

import frappe


def handle_incoming(message) -> None:
	"""
	Save the answers of a completed flow and create the configured document.

	Parameters:
	        message (Document, required): The incoming WhatsApp Message.

	Returns:
	        None
	"""
	if message.message_type != "flow":
		return
	answers = json.loads(message.payload or "{}")
	token = answers.get("flow_token")
	flow = find_flow_by_token(token)
	response = frappe.get_doc(
		{
			"doctype": "WhatsApp Flow Response",
			"flow": flow,
			"phone_number": message.phone_number,
			"flow_token": token,
			"message": message.name,
			"answers": json.dumps(answers),
		}
	)
	if flow:
		__create_document(response, flow, answers)
	response.insert(ignore_permissions=True)
	if flow:
		frappe.publish_realtime(
			"whatsapp_flow_response",
			{"flow": flow, "response": response.name, "phone_number": message.phone_number},
			doctype="WhatsApp Flow",
			docname=flow,
			after_commit=True,
		)


def find_flow_by_token(token: str | None) -> str | None:
	"""
	Find the flow that was sent with a flow token.

	Parameters:
	        token (str, optional): The flow token from the answers.

	Returns:
	        str | None: The WhatsApp Flow name.
	"""
	if not token:
		return None
	payload = frappe.db.get_value(
		"WhatsApp Message",
		{"direction": "Outgoing", "message_type": "flow", "payload": ["like", f'%"{token}"%']},
		"payload",
	)
	return json.loads(payload).get("flow") if payload else None


def __create_document(response, flow: str, answers: dict) -> None:
	"""
	Create a document of the flow's target doctype from the mapped answers.

	An error is kept on the response instead of losing the answers.

	Parameters:
	        response (Document, required): The new WhatsApp Flow Response.
	        flow (str, required): The WhatsApp Flow name.
	        answers (dict, required): The answers by field name.

	Returns:
	        None
	"""
	settings = frappe.get_doc("WhatsApp Flow", flow)
	if not settings.target_doctype:
		return
	values = {
		row.target_field: answers.get(row.field_name)
		for row in settings.components
		if row.target_field and row.field_name in answers
	}
	try:
		doc = frappe.get_doc({"doctype": settings.target_doctype, **values}).insert(
			ignore_permissions=True
		)
		response.reference_doctype, response.reference_name = doc.doctype, doc.name
	except Exception as error:
		frappe.clear_last_message()
		response.error = str(error)
