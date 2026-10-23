# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_flow import keys, sending
from whatsapp_connect.whatsapp_connect_flow.doctype.whatsapp_flow import flow_meta


@frappe.whitelist(methods=["POST"])
def save_to_meta(flow: str):
	"""
	        Create the flow in Meta (or update it) and upload its Flow JSON.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.flow.save_to_meta`
	        **HTTP Method:** POST
	        **Parameters:**
	                - flow (str, required): The WhatsApp Flow name
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Saved to Meta", "data": {"validation_errors": []}, "errors": null}
	```
	"""
	errors = flow_meta.save_to_meta(flow)
	message = _("Saved to Meta with validation errors") if errors else _("Saved to Meta")
	return api_response(
		status=not errors,
		code=422 if errors else 200,
		message=message,
		data={"validation_errors": errors},
	)


@frappe.whitelist(methods=["POST"])
def publish(flow: str):
	"""
	        Publish the flow in Meta. A published flow cannot be changed.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.flow.publish`
	        **HTTP Method:** POST
	        **Parameters:**
	                - flow (str, required): The WhatsApp Flow name
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Status: Published", "data": {"status": "Published"}, "errors": null}
	```
	"""
	status = flow_meta.publish(flow)
	return api_response(message=_("Status: {0}").format(_(status)), data={"status": status})


@frappe.whitelist(methods=["POST"])
def deprecate(flow: str):
	"""
	        Deprecate a published flow, so that it can no longer be sent.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.flow.deprecate`
	        **HTTP Method:** POST
	        **Parameters:**
	                - flow (str, required): The WhatsApp Flow name
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Status: Deprecated", "data": {"status": "Deprecated"}, "errors": null}
	```
	"""
	status = flow_meta.deprecate(flow)
	return api_response(message=_("Status: {0}").format(_(status)), data={"status": status})


@frappe.whitelist(methods=["POST"])
def refresh_status(flow: str):
	"""
	        Read the flow's status, validation errors and preview link from Meta.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.flow.refresh_status`
	        **HTTP Method:** POST
	        **Parameters:**
	                - flow (str, required): The WhatsApp Flow name
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "", "data": {"status": "DRAFT", "preview": {"preview_url": "https://..."}}, "errors": null}
	```
	"""
	return api_response(data=flow_meta.refresh_status(flow))


@frappe.whitelist(methods=["POST"])
def import_flows(account: str):
	"""
	        Create or update local flows from the account's flows in Meta, with their Flow JSON.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.flow.import_flows`
	        **HTTP Method:** POST
	        **Parameters:**
	                - account (str, required): The WhatsApp Account name
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "3 flows imported", "data": {"count": 3}, "errors": null}
	```
	"""
	count = flow_meta.import_flows(account)
	return api_response(message=_("{0} flows imported").format(count), data={"count": count})


@frappe.whitelist(methods=["POST"])
def send(flow: str, to: str, text: str | None = None):
	"""
	        Send a flow to a number. A draft flow is sent in draft mode (test numbers only).

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.flow.send`
	        **HTTP Method:** POST
	        **Parameters:**
	                - flow (str, required): The WhatsApp Flow name
	                - to (str, required): The recipient's number
	                - text (str, optional): Text above the button
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Message status: Sent", "data": {"message": "a1b2c3", "status": "Sent"}, "errors": null}
	```
	"""
	frappe.get_doc("WhatsApp Flow", flow).check_permission("read")
	frappe.has_permission("WhatsApp Message", "create", throw=True)
	message = sending.send_flow(flow, to, text)
	failed = message.status in ("Failed", "Opted Out")
	return api_response(
		status=not failed,
		code=422 if failed else 200,
		message=message.error_message or _("Message status: {0}").format(_(message.status)),
		data={"message": message.name, "status": message.status},
	)


@frappe.whitelist(methods=["POST"])
def generate_keys(account: str):
	"""
	        Create the account's Flow key pair and register the public key in Meta. Needed
	        for flows that use the data endpoint. Replaces an earlier key.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.flow.generate_keys`
	        **HTTP Method:** POST
	        **Parameters:**
	                - account (str, required): The WhatsApp Account name
	        **Response:**
	```json
	                {"status": true, "status_code": 200, "message": "Flow keys created and registered in Meta", "data": null, "errors": null}
	```
	"""
	keys.generate_flow_keys(account)
	return api_response(message=_("Flow keys created and registered in Meta"))
