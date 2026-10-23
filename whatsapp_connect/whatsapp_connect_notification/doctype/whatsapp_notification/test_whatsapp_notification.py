# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import json
from unittest.mock import patch

import frappe

from whatsapp_connect.tests.utils import (
	MINIMAL_PDF,
	REQUESTS,
	IntegrationTestCase,
	graph_response,
	make_account,
	make_template,
	random_number,
)
from whatsapp_connect.whatsapp_connect_core.messaging.opt_out import set_opted_out
from whatsapp_connect.whatsapp_connect_notification import tasks
from whatsapp_connect.whatsapp_connect_notification.doctype.whatsapp_notification.notification_utils import (
	clear_notification_map,
	get_notification_map,
)
from whatsapp_connect.whatsapp_connect_notification.sending import send_notification

GET_PRINT = "whatsapp_connect.whatsapp_connect_notification.attachments.frappe.get_print"


class TestWhatsAppNotification(IntegrationTestCase):
	"""Events, recipients, conditions, attachments and schedules."""

	def setUp(self):
		"""Create the account, an approved template, and a contact with a mobile number."""
		self.account = make_account()
		self.template = make_template("test_notify", body_fields="first_name\nlast_name")
		self.number = random_number()
		self.contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Asha",
				"last_name": "Traders",
				"phone_nos": [{"phone": f"+{self.number}", "is_primary_mobile_no": 1}],
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		"""Undo the test's database changes; the cached event map is not rolled back."""
		frappe.db.rollback()
		clear_notification_map()

	def notification(self, **values):
		"""Create a WhatsApp Notification on Contact."""
		return frappe.get_doc(
			{
				"doctype": "WhatsApp Notification",
				"notification_name": f"Test {frappe.generate_hash(length=6)}",
				"event_type": "Document Event",
				"reference_doctype": "Contact",
				"document_event": "Save",
				"template": self.template,
				"phone_field": "mobile_no",
				**values,
			}
		).insert(ignore_permissions=True)

	def run_send(self, notification, doc=None):
		"""Send with the Graph API mocked; return (sent count, request mock)."""
		with patch(
			REQUESTS, return_value=graph_response({"messages": [{"id": "wamid.N"}], "id": "media-1"})
		) as request:
			sent = send_notification(notification.name, "Contact", (doc or self.contact).name)
		return sent, request

	def test_send_to_phone_field_with_values(self):
		sent, request = self.run_send(self.notification())
		self.assertEqual(sent, 1)
		body = request.call_args.kwargs["json"]
		self.assertEqual(body["to"], self.number)
		self.assertEqual(
			[p["text"] for p in body["template"]["components"][0]["parameters"]], ["Asha", "Traders"]
		)
		message = frappe.get_last_doc("WhatsApp Message", filters={"phone_number": self.number})
		self.assertTrue(message.source.startswith("Notification: "))

	def test_condition(self):
		sent, request = self.run_send(self.notification(condition="doc.first_name == 'Ravi'"))
		self.assertEqual(sent, 0)
		request.assert_not_called()

	def test_notification_fields_override_template_mapping(self):
		_sent, request = self.run_send(self.notification(body_fields="last_name\nfirst_name"))
		parameters = request.call_args.kwargs["json"]["template"]["components"][0]["parameters"]
		self.assertEqual([p["text"] for p in parameters], ["Traders", "Asha"])

	def test_opted_out_and_duplicate_numbers_are_skipped(self):
		other = random_number()
		set_opted_out(other, True, self.account)
		sent, request = self.run_send(self.notification(fixed_numbers=f"+{self.number}\n{other}"))
		self.assertEqual((sent, request.call_count), (1, 1))

	def test_role_recipients_with_condition(self):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"{frappe.generate_hash(length=8)}@example.com",
				"first_name": "Role",
				"mobile_no": f"+{random_number()}",
				"send_welcome_email": 0,
				"roles": [{"role": "Accounts User"}],
			}
		).insert(ignore_permissions=True)
		notification = self.notification(
			phone_field=None,
			recipient_roles=[{"role": "Accounts User", "condition": "doc.first_name == 'Asha'"}],
		)
		_sent, request = self.run_send(notification)
		self.assertIn(
			user.mobile_no.lstrip("+"), [call.kwargs["json"]["to"] for call in request.call_args_list]
		)

	def test_set_field_after_sending(self):
		self.run_send(self.notification(set_field="designation", set_value="Notified"))
		self.assertEqual(frappe.db.get_value("Contact", self.contact.name, "designation"), "Notified")

	def test_print_is_uploaded_as_document_header(self):
		template = make_template("test_notify_print", header_type="Document")
		notification = self.notification(template=template, attach_print=1)
		with patch(GET_PRINT, return_value=MINIMAL_PDF) as get_print:
			_sent, request = self.run_send(notification)
		get_print.assert_called_once()
		upload, send = request.call_args_list
		self.assertTrue(upload.args[1].endswith("/media"))
		header = send.kwargs["json"]["template"]["components"][0]
		self.assertEqual(header["parameters"][0]["document"]["id"], "media-1")

	def test_events_queue_matching_notifications(self):
		notification = self.notification()
		self.assertIn(notification.name, get_notification_map()["Contact"]["Save"])
		with patch(REQUESTS, return_value=graph_response({"messages": [{"id": "wamid.E"}]})) as request:
			self.contact.designation = "Buyer"
			self.contact.save(ignore_permissions=True)
		self.assertTrue(request.called)

	def test_value_change_event(self):
		self.notification(document_event="Value Change", value_changed="designation")
		with patch(REQUESTS, return_value=graph_response({"messages": [{"id": "wamid.V"}]})) as request:
			self.contact.department = "x"
			self.contact.save(ignore_permissions=True)
			self.assertFalse(request.called)
			self.contact.designation = "Owner"
			self.contact.save(ignore_permissions=True)
		self.assertTrue(request.called)

	def test_disabling_updates_the_map(self):
		notification = self.notification()
		notification.enabled = 0
		notification.save(ignore_permissions=True)
		self.assertNotIn(notification.name, get_notification_map().get("Contact", {}).get("Save", []))

	def test_validation(self):
		with self.assertRaises(frappe.ValidationError):
			self.notification(phone_field=None)
		with self.assertRaises(frappe.ValidationError):
			self.notification(phone_field="no_such_field")

	def test_scheduled_with_filters(self):
		notification = self.notification(
			event_type="Scheduled",
			frequency="Daily",
			document_filters=json.dumps({"name": self.contact.name}),
		)
		with patch(REQUESTS, return_value=graph_response({"messages": [{"id": "wamid.S"}]})) as request:
			tasks.run_scheduled("Daily")
		self.assertEqual(request.call_args.kwargs["json"]["to"], self.number)
		self.assertTrue(notification.name)
