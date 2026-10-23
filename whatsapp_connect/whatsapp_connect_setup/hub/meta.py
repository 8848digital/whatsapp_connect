# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Meta calls that the hub makes during Embedded Signup."""

import requests

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_setup.graph import TokenGraph


def exchange_code(settings, code: str) -> str:
	"""
	Exchange the popup's code for the business token. The call is not logged: its answer is the token.

	Parameters:
	        settings (Document, required): WhatsApp Hub Settings.
	        code (str, required): The code from the popup.

	Returns:
	        str: The business integration system user token.
	"""
	url = f"{settings.graph_api_url.rstrip('/')}/{settings.graph_api_version}/oauth/access_token"
	params = {
		"client_id": settings.app_id,
		"client_secret": settings.get_password("app_secret"),
		"code": code,
	}
	try:
		answer = requests.get(url, params=params, timeout=30).json()
	except (requests.RequestException, ValueError) as exc:
		frappe.throw(_("Could not reach Meta: {0}").format(exc))
	if not answer.get("access_token"):
		frappe.throw(_("Meta refused the code: {0}").format((answer.get("error") or {}).get("message")))
	return answer["access_token"]


def find_number(graph: TokenGraph, waba_id: str, phone_number_id: str) -> dict:
	"""
	Check that the phone number belongs to the business account.

	Parameters:
	        graph (TokenGraph, required): Client with the business token.
	        waba_id (str, required): The business account ID.
	        phone_number_id (str, required): The phone number ID.

	Returns:
	        dict: The phone number from Meta.
	"""
	fields = "id,display_phone_number,verified_name"
	numbers = graph.request("GET", f"{waba_id}/phone_numbers", params={"fields": fields})
	for number in numbers.get("data") or []:
		if number.get("id") == phone_number_id:
			return number
	frappe.throw(_("The phone number is not in the business account"))
