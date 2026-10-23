# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Auto-reply actions: functions that answer with data, for example the status of an order.

Apps add actions with a hook in their hooks.py:

	whatsapp_connect_auto_reply_actions = {"Delivery Date": "my_app.whatsapp.delivery_date"}

An action gets the incoming WhatsApp Message and returns the reply text.
"""

import frappe


def get_actions() -> dict[str, str]:
	"""
	Return the registered actions by name.

	Returns:
	        dict[str, str]: {"Order Status": "dotted.path", ...}; a later app wins a name.
	"""
	hooks = frappe.get_hooks("whatsapp_connect_auto_reply_actions") or {}
	return {name: paths[-1] if isinstance(paths, list) else paths for name, paths in hooks.items()}


def run_action(name: str, message) -> str:
	"""
	Run an action for an incoming message.

	Parameters:
	        name (str, required): The action name.
	        message (Document, required): The incoming WhatsApp Message.

	Returns:
	        str: The reply text.
	"""
	return frappe.get_attr(get_actions()[name])(message)
