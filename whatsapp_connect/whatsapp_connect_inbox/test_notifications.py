# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe

from whatsapp_connect.tests.webhook_case import WebhookTestCase
from whatsapp_connect.whatsapp_connect_inbox import notifications

ENQUEUE_NOTIFICATION = (
	"frappe.desk.doctype.notification_log.notification_log.enqueue_create_notification"
)


class TestInboxNotifications(WebhookTestCase):
	"""Popups and desk notifications for new messages."""

	def setUp(self):
		"""Notify the assignee, else all agents (the default)."""
		super().setUp()
		frappe.db.set_single_value(
			"WhatsApp Settings", "inbox_notifications", notifications.NOTIFY_ASSIGNEE_OR_ALL
		)
		self.agent = self.make_agent("wac.agent@example.com")

	def make_agent(self, email: str) -> str:
		"""Create an enabled user with the WhatsApp User role."""
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": "Agent", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
			user.add_roles("WhatsApp User")
		return email

	def receive(self, body: str, **values):
		"""Post one incoming text message and return the popups and desk notifications sent."""
		with patch("frappe.publish_realtime") as publish, patch(ENQUEUE_NOTIFICATION) as notify:
			self.incoming({"type": "text", "text": {"body": body}, **values})
		popups = [c for c in publish.call_args_list if c.args[0] == notifications.POPUP_EVENT]
		return popups, notify

	def test_unassigned_conversation_notifies_all_agents_once(self):
		popups, notify = self.receive("Hi")
		self.assertIn(self.agent, [c.kwargs["user"] for c in popups])
		self.assertEqual(popups[0].args[1]["phone_number"], self.number)
		users, doc = notify.call_args.args
		self.assertIn(self.agent, users)
		self.assertEqual(doc["link"], f"/app/whatsapp-inbox/{self.number}")

		# The second unread message shows a popup but adds no second desk notification.
		popups, notify = self.receive("Are you there?")
		self.assertTrue(popups)
		notify.assert_not_called()

	def test_assigned_conversation_notifies_only_the_assignee(self):
		self.incoming({"type": "text", "text": {"body": "Hi"}})
		other = self.make_agent("wac.other@example.com")
		frappe.db.set_value("WhatsApp Profile", self.number, {"assigned_to": other, "unread_count": 0})
		popups, notify = self.receive("Hello again")
		self.assertEqual([c.kwargs["user"] for c in popups], [other])
		self.assertEqual(notify.call_args.args[0], [other])

	def test_nobody_setting_turns_notifications_off(self):
		frappe.db.set_single_value("WhatsApp Settings", "inbox_notifications", "Nobody")
		popups, notify = self.receive("Hi")
		self.assertEqual(popups, [])
		notify.assert_not_called()
