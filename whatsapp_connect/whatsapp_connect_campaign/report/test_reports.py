# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe

from whatsapp_connect.tests.utils import (
	IntegrationTestCase,
	make_account,
	make_template,
	random_number,
)
from whatsapp_connect.whatsapp_connect_campaign.report.whatsapp_campaign_recipients import (
	whatsapp_campaign_recipients,
)
from whatsapp_connect.whatsapp_connect_campaign.report.whatsapp_delivery_summary import (
	whatsapp_delivery_summary,
)


class TestReports(IntegrationTestCase):
	"""Delivery summary and campaign recipients."""

	def setUp(self):
		"""Create messages with each status for one template and campaign (not sent to Meta)."""
		self.account = make_account()
		self.template = make_template("test_report_tpl")
		self.campaign = f"TEST-CAMP-{frappe.generate_hash(length=6)}"
		for status in ("Sent", "Delivered", "Read", "Read", "Failed", "Opted Out"):
			message = frappe.get_doc(
				{
					"doctype": "WhatsApp Message",
					"phone_number": random_number(),
					"message_type": "template",
					"template": self.template,
					"status": status,
					"campaign": self.campaign,
					"whatsapp_account": self.account,
				}
			)
			message.flags.skip_send = True
			message.insert(ignore_permissions=True)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_delivery_summary(self):
		columns, data, _message, chart = whatsapp_delivery_summary.execute(
			{"group_by": "Campaign", "whatsapp_account": self.account}
		)
		row = next(row for row in data if row.group == self.campaign)
		self.assertEqual(
			(row.total, row.sent, row.delivered, row.read, row.failed, row.opted_out), (6, 4, 3, 2, 1, 1)
		)
		self.assertEqual((row.delivery_rate, row.read_rate), (75.0, 66.7))
		self.assertEqual((columns[0]["label"], chart["type"]), ("Campaign", "bar"))

	def test_campaign_recipients(self):
		_columns, data = whatsapp_campaign_recipients.execute(
			{"campaign": self.campaign, "status": "Read"}
		)
		self.assertEqual(len(data), 2)
		self.assertEqual(whatsapp_campaign_recipients.execute({})[1], [])
