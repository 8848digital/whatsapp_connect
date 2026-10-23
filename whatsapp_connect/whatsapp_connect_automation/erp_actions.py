# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Built-in auto-reply actions that read ERPNext data of the customer who wrote.

The customer is found by the phone number: the Customer of the message, or the
Customer linked to its Contact.
"""

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, formatdate, getdate

MAX_ROWS = 5
NOT_FOUND = "We could not find an account with this number. An agent will reply soon."


def order_status(message) -> str:
	"""
	Reply with the open Sales Orders of the customer, with delivery date and progress.

	Parameters:
	        message (Document, required): The incoming WhatsApp Message.

	Returns:
	        str: The reply text.
	"""
	customer = get_customer(message)
	if not customer or not frappe.db.exists("DocType", "Sales Order"):
		return _(NOT_FOUND)
	orders = frappe.get_all(
		"Sales Order",
		filters={"customer": customer, "docstatus": 1, "status": ["not in", ["Completed", "Closed"]]},
		fields=["name", "status", "delivery_date", "per_delivered", "grand_total", "currency"],
		order_by="transaction_date desc",
		limit=MAX_ROWS,
	)
	if not orders:
		return _("You have no open orders.")
	lines = [
		_("*{0}*: {1}, {2}% delivered, due {3}").format(
			order.name,
			_(order.status),
			int(flt(order.per_delivered)),
			formatdate(order.delivery_date) if order.delivery_date else _("not set"),
		)
		for order in orders
	]
	return "\n".join([_("Your open orders:"), *lines])


def outstanding_balance(message) -> str:
	"""
	Reply with the unpaid Sales Invoices of the customer and the total due.

	Parameters:
	        message (Document, required): The incoming WhatsApp Message.

	Returns:
	        str: The reply text.
	"""
	customer = get_customer(message)
	if not customer or not frappe.db.exists("DocType", "Sales Invoice"):
		return _(NOT_FOUND)
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "due_date", "outstanding_amount", "currency"],
		order_by="due_date asc",
	)
	if not invoices:
		return _("You have nothing to pay. Thank you.")
	currency = invoices[0].currency
	total = sum(flt(invoice.outstanding_amount) for invoice in invoices)
	today = getdate()
	lines = [
		_("*{0}*: {1}, due {2}{3}").format(
			invoice.name,
			fmt_money(invoice.outstanding_amount, currency=invoice.currency),
			formatdate(invoice.due_date),
			_(" (overdue)") if invoice.due_date and getdate(invoice.due_date) < today else "",
		)
		for invoice in invoices[:MAX_ROWS]
	]
	return "\n".join([_("Amount due: *{0}*").format(fmt_money(total, currency=currency)), *lines])


def get_customer(message) -> str | None:
	"""
	Return the Customer of a message: its reference, or the Customer of its Contact.

	Parameters:
	        message (Document, required): The WhatsApp Message.

	Returns:
	        str | None: The Customer name.
	"""
	if message.reference_doctype == "Customer":
		return message.reference_name
	if message.reference_doctype != "Contact":
		return None
	customers = frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Contact",
			"parent": message.reference_name,
			"link_doctype": "Customer",
		},
		pluck="link_name",
		limit=1,
	)
	return customers[0] if customers else None
