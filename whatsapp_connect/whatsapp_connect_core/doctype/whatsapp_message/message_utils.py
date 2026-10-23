# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Business logic for WhatsApp Message."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_account.account_utils import (
	get_default_account,
)
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_profile.profile_utils import (
	get_or_create_profile,
)
from whatsapp_connect.whatsapp_connect_core.messaging import sender
from whatsapp_connect.whatsapp_connect_core.messaging.contact_link import find_reference
from whatsapp_connect.whatsapp_connect_core.messaging.conversation import publish, record_message
from whatsapp_connect.whatsapp_connect_core.phone import normalize_number


def prepare_message(message) -> None:
	"""
	Set defaults before the message is inserted.

	Parameters:
	        message (Document, required): The new WhatsApp Message.

	Returns:
	        None
	"""
	number = normalize_number(message.phone_number)
	if not number:
		frappe.throw(_("{0} is not a valid phone number").format(message.phone_number))
	message.phone_number = number

	if not message.whatsapp_account:
		message.whatsapp_account = get_default_account(message.direction.lower())
	if not message.whatsapp_account:
		frappe.throw(_("Set a default WhatsApp Account for {0} messages").format(_(message.direction)))

	if message.direction == "Incoming":
		message.status = "Received"
		__link_reference(message)
	elif message.status in (None, "", "Draft"):
		message.status = "Queued"

	message.profile = get_or_create_profile(number, account=message.whatsapp_account)
	__link_profile_contact(message)


def send_after_insert(message) -> None:
	"""
	Update the conversation, then send a queued outgoing message unless the caller
	asked not to (flags.skip_send).

	Parameters:
	        message (Document, required): The inserted WhatsApp Message.

	Returns:
	        None
	"""
	record_message(message)
	if message.direction != "Outgoing" or message.status != "Queued" or message.flags.skip_send:
		return
	sender.send(message)


def retry_message(message_name: str) -> str:
	"""
	Send a failed outgoing message again.

	Parameters:
	        message_name (str, required): The WhatsApp Message name.

	Returns:
	        str: The new status.
	"""
	message = frappe.get_doc("WhatsApp Message", message_name)
	message.check_permission("write")
	if message.direction != "Outgoing" or message.status != "Failed":
		frappe.throw(_("Only failed outgoing messages can be sent again"))
	sender.send(message)
	publish(message.name, message.phone_number, "status")
	return frappe.db.get_value("WhatsApp Message", message_name, "status")


def mark_as_read(message_name: str) -> None:
	"""
	Mark an incoming message as read, for a user who can read the message.

	Parameters:
	        message_name (str, required): The WhatsApp Message name.

	Returns:
	        None
	"""
	frappe.get_doc("WhatsApp Message", message_name).check_permission("read")
	send_read_receipt(message_name)


def send_read_receipt(message_name: str) -> None:
	"""
	Mark an incoming message as read in the customer's WhatsApp (blue ticks).

	Also runs as a background job after a webhook call, without a user session.

	Parameters:
	        message_name (str, required): The WhatsApp Message name.

	Returns:
	        None
	"""
	message = frappe.get_doc("WhatsApp Message", message_name)
	if message.direction != "Incoming" or not message.wamid:
		frappe.throw(_("Only received messages can be marked as read"))
	CloudAPI(message.whatsapp_account).mark_as_read(message.wamid)


def __link_reference(message) -> None:
	"""
	Link an incoming message to the Contact, Lead or Customer with the same number.

	Parameters:
	        message (Document, required): An incoming WhatsApp Message.

	Returns:
	        None
	"""
	if message.reference_doctype:
		return
	doctype, name = find_reference(message.phone_number)
	if doctype:
		message.reference_doctype, message.reference_name = doctype, name


def __link_profile_contact(message) -> None:
	"""
	Store the message's Contact on the WhatsApp Profile when the profile has none.

	Parameters:
	        message (Document, required): The WhatsApp Message.

	Returns:
	        None
	"""
	if message.reference_doctype != "Contact" or not message.reference_name:
		return
	if not frappe.db.get_value("WhatsApp Profile", message.profile, "contact"):
		frappe.db.set_value(
			"WhatsApp Profile", message.profile, "contact", message.reference_name, update_modified=False
		)
