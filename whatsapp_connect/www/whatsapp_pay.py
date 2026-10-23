# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Open the payment page of a payment link button (https://<site>/whatsapp_pay?t=<token>)."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_payment.payment_link import resolve_token

no_cache = 1


def get_context(context):
	"""
	Redirect to the payment URL of a valid token; otherwise show that the link is not valid.

	Parameters:
	        context (dict, required): The page context.

	Returns:
	        dict: The context with title and message, when the token is not valid.
	"""
	url = resolve_token(frappe.form_dict.get("t"))
	if url:
		frappe.local.flags.redirect_location = url
		raise frappe.Redirect
	context.title = _("Payment link")
	context.no_breadcrumbs = 1
	context.message = _("This payment link is not valid, or the payment is already done.")
	return context
