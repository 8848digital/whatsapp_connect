# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Payment links in templates: the URL of an ERPNext Payment Request for the document.

Template mappings use two names (whatsapp_connect_value_providers hook):
- payment_link: the full payment URL, for a body variable.
- payment_link_token: a signed token for a dynamic URL button whose URL is
  https://<site>/whatsapp_pay?t={{1}}. The /whatsapp_pay page opens the payment URL.
"""

import hashlib
import hmac

import frappe
from frappe import _
from frappe.utils.password import get_encryption_key

PAYABLE_DOCTYPES = ("Sales Invoice", "Sales Order")
OPEN_STATUSES = ("Initiated", "Requested", "Partially Paid")
TOKEN_SEPARATOR = "~"
SIGNATURE_LENGTH = 24


def payment_link(doc) -> str:
	"""
	Return the payment URL for a Sales Invoice, Sales Order or Payment Request (value provider).

	Parameters:
	        doc (Document, required): The document the message is about.

	Returns:
	        str: The payment URL; a placeholder in a preview.
	"""
	if frappe.flags.whatsapp_connect_preview:
		return _("(payment link)")
	return get_payment_request(doc).payment_url


def payment_link_token(doc) -> str:
	"""
	Return the signed token of the document's Payment Request, for a dynamic URL button.

	Parameters:
	        doc (Document, required): The document the message is about.

	Returns:
	        str: "<Payment Request name>~<signature>"; a placeholder in a preview.
	"""
	if frappe.flags.whatsapp_connect_preview:
		return _("(payment link)")
	name = get_payment_request(doc).name
	return f"{name}{TOKEN_SEPARATOR}{__sign(name)}"


def resolve_token(token: str | None) -> str | None:
	"""
	Return the payment URL of a token, or None when the token is not valid.

	Parameters:
	        token (str, optional): A token from payment_link_token.

	Returns:
	        str | None: The payment URL of an open Payment Request.
	"""
	name, _separator, signature = (token or "").rpartition(TOKEN_SEPARATOR)
	if not name or not hmac.compare_digest(signature, __sign(name)):
		return None
	request = frappe.db.get_value(
		"Payment Request", {"name": name, "docstatus": 1}, ["payment_url", "status"], as_dict=True
	)
	if not request or request.status not in OPEN_STATUSES:
		return None
	return request.payment_url


def get_payment_request(doc):
	"""
	Return the open, submitted Payment Request of a document; make one when there is none.

	Parameters:
	        doc (Document, required): A Sales Invoice, Sales Order or Payment Request.

	Returns:
	        Document: The Payment Request, with a payment URL.
	"""
	if doc.doctype == "Payment Request":
		request = doc
	elif doc.doctype in PAYABLE_DOCTYPES:
		request = __existing_request(doc) or __make_request(doc)
	else:
		frappe.throw(
			_("Payment links work for {0}").format(", ".join(PAYABLE_DOCTYPES + ("Payment Request",)))
		)
	if not request.get("payment_url"):
		frappe.throw(
			_("Payment Request {0} has no payment URL. Set up a Payment Gateway Account.").format(
				request.name
			)
		)
	return request


def __existing_request(doc):
	"""
	Return the latest open, submitted Payment Request with a payment URL for a document.

	Parameters:
	        doc (Document, required): A Sales Invoice or Sales Order.

	Returns:
	        Document | None: The Payment Request.
	"""
	name = frappe.db.get_value(
		"Payment Request",
		{
			"reference_doctype": doc.doctype,
			"reference_name": doc.name,
			"docstatus": 1,
			"status": ["in", OPEN_STATUSES],
			"payment_url": ["is", "set"],
		},
		order_by="creation desc",
	)
	return frappe.get_doc("Payment Request", name) if name else None


def __make_request(doc):
	"""
	Make and submit a Payment Request with ERPNext, without sending its email.

	Parameters:
	        doc (Document, required): A submitted Sales Invoice or Sales Order.

	Returns:
	        Document: The Payment Request.
	"""
	from erpnext.accounts.doctype.payment_request.payment_request import make_payment_request

	if doc.docstatus != 1:
		frappe.throw(_("Submit {0} {1} before you send a payment link").format(_(doc.doctype), doc.name))
	return make_payment_request(dt=doc.doctype, dn=doc.name, submit_doc=1, mute_email=1, return_doc=1)


def __sign(name: str) -> str:
	"""
	Sign a Payment Request name with the site's encryption key.

	Parameters:
	        name (str, required): The Payment Request name.

	Returns:
	        str: The first characters of the HMAC-SHA256 hex digest.
	"""
	digest = hmac.new(get_encryption_key().encode(), name.encode(), hashlib.sha256).hexdigest()
	return digest[:SIGNATURE_LENGTH]
