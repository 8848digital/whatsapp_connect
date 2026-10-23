# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from whatsapp_connect.utils.api_handlers.envelope import api_response
from whatsapp_connect.whatsapp_connect_setup import (
	account_setup,
	discovery,
	hub_client,
	manual_setup,
	setup_checks,
)

SETUP_ROLES = ["System Manager", "WhatsApp Manager"]


@frappe.whitelist(methods=["GET"])
def get_status():
	"""
	        The WhatsApp Accounts of the site and whether Connect with Facebook is available.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.setup.get_status`
	        **HTTP Method:** GET
	        **Parameters:** none
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Setup status",
	                        "data": {"accounts": [], "hub_url": "https://hub.example.com", "site_url": "https://erp.example.com"},
	                        "errors": null
	                }
	```
	"""
	frappe.only_for(SETUP_ROLES)
	return api_response(message=_("Setup status"), data=setup_checks.list_accounts())


@frappe.whitelist(methods=["POST"])
def start_hub_signup(coexistence: int = 0):
	"""
	        Open an Embedded Signup session on the hub. The browser opens signup_url in a popup.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.setup.start_hub_signup`
	        **HTTP Method:** POST
	        **Parameters:**
	                - coexistence (int, optional): 1 when the number stays on the WhatsApp Business app
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Signup started",
	                        "data": {"session": "3f2a...", "signup_url": "https://hub.example.com/whatsapp_signup?session=3f2a..."},
	                        "errors": null
	                }
	```
	"""
	frappe.only_for(SETUP_ROLES)
	return api_response(message=_("Signup started"), data=hub_client.start_signup(coexistence))


@frappe.whitelist(methods=["POST"])
def complete_hub_signup(session: str):
	"""
	        Get the finished signup from the hub, save the WhatsApp Account and run the setup steps.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.setup.complete_hub_signup`
	        **HTTP Method:** POST
	        **Parameters:**
	                - session (str, required): The session from start_hub_signup
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "WhatsApp is connected",
	                        "data": {"account": "Asha Traders", "steps": [{"step": "Register the number", "ok": true, "message": "Registered"}]},
	                        "errors": null
	                }
	```
	"""
	frappe.only_for(SETUP_ROLES)
	return api_response(message=_("WhatsApp is connected"), data=hub_client.complete_signup(session))


@frappe.whitelist(methods=["POST"])
def discover_numbers(app_id: str, app_secret: str, access_token: str):
	"""
	        Check the credentials of an own Meta app and list the business accounts and numbers.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.setup.discover_numbers`
	        **HTTP Method:** POST
	        **Parameters:**
	                - app_id (str, required): The Meta App ID
	                - app_secret (str, required): The Meta App Secret
	                - access_token (str, required): A system user token of the app
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "The token is valid",
	                        "data": {"expires_at": 0, "accounts": [{"id": "1029", "name": "Asha Traders", "phone_numbers": [{"id": "1123", "display_phone_number": "+91 98765 43210"}]}]},
	                        "errors": null
	                }
	```
	"""
	frappe.only_for(SETUP_ROLES)
	found = discovery.discover(app_id, app_secret, access_token)
	return api_response(message=_("The token is valid"), data=found)


@frappe.whitelist(methods=["POST"])
def connect_own_app(
	app_id: str, app_secret: str, access_token: str, phone_number_id: str, register_number: int = 0
):
	"""
	        Save the WhatsApp Account of an own Meta app, set the webhook and run the setup steps.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.setup.connect_own_app`
	        **HTTP Method:** POST
	        **Parameters:**
	                - app_id (str, required): The Meta App ID
	                - app_secret (str, required): The Meta App Secret
	                - access_token (str, required): A system user token of the app
	                - phone_number_id (str, required): The number to connect
	                - register_number (int, optional): 1 to register the number for the Cloud API
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "WhatsApp is connected",
	                        "data": {"account": "Asha Traders", "steps": [], "expires_at": 0},
	                        "errors": null
	                }
	```
	"""
	frappe.only_for(SETUP_ROLES)
	result = manual_setup.connect_own_app(
		app_id, app_secret, access_token, phone_number_id, register_number
	)
	return api_response(message=_("WhatsApp is connected"), data=result)


@frappe.whitelist(methods=["POST"])
def run_steps(account: str):
	"""
	        Run the setup steps again on an account (register, webhooks, templates, Flow keys).

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.setup.run_steps`
	        **HTTP Method:** POST
	        **Parameters:**
	                - account (str, required): The WhatsApp Account name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Setup steps finished",
	                        "data": {"steps": [{"step": "Sync templates", "ok": true, "message": "4 templates synced"}]},
	                        "errors": null
	                }
	```
	"""
	frappe.only_for(SETUP_ROLES)
	steps = account_setup.run_setup_steps(account, register_number=False)
	return api_response(message=_("Setup steps finished"), data={"steps": steps})


@frappe.whitelist(methods=["POST"])
def send_test(account: str, to: str):
	"""
	        Send the hello_world template of an account to a number.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.setup.send_test`
	        **HTTP Method:** POST
	        **Parameters:**
	                - account (str, required): The WhatsApp Account name
	                - to (str, required): The phone number, with the country code
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Test message sent",
	                        "data": {"message": "WA-MSG-00012", "status": "Sent"},
	                        "errors": null
	                }
	```
	"""
	frappe.only_for(SETUP_ROLES)
	return api_response(message=_("Test message sent"), data=setup_checks.send_test(account, to))


@frappe.whitelist(methods=["GET"])
def check_incoming(account: str, since: str):
	"""
	        Tell if the account received a message after a time (the webhook test).

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.setup.check_incoming`
	        **HTTP Method:** GET
	        **Parameters:**
	                - account (str, required): The WhatsApp Account name
	                - since (str, required): Datetime in the site's time zone
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Checked",
	                        "data": {"found": true, "phone_number": "919876543210", "body": "Hi"},
	                        "errors": null
	                }
	```
	"""
	frappe.only_for(SETUP_ROLES)
	return api_response(message=_("Checked"), data=setup_checks.incoming_since(account, since))


@frappe.whitelist(methods=["POST"])
def disconnect_hub(account: str):
	"""
	        Stop the hub forwarding webhooks to an Embedded Signup account, and disable the account.

	        **Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.setup.disconnect_hub`
	        **HTTP Method:** POST
	        **Parameters:**
	                - account (str, required): The WhatsApp Account name
	        **Response:**
	```json
	                {
	                        "status": true,
	                        "status_code": 200,
	                        "message": "Disconnected from the hub",
	                        "data": null,
	                        "errors": null
	                }
	```
	"""
	frappe.only_for(SETUP_ROLES)
	hub_client.disconnect(account)
	return api_response(message=_("Disconnected from the hub"))
