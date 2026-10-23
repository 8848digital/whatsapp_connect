# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe
from frappe.utils import add_to_date, now_datetime

from whatsapp_connect.tests.utils import (
	REQUESTS,
	IntegrationTestCase,
	graph_response,
	make_account,
	make_template,
	random_number,
)
from whatsapp_connect.whatsapp_connect_campaign import campaign_sender, tasks
from whatsapp_connect.whatsapp_connect_core.messaging.opt_out import set_opted_out

OK = {"messages": [{"id": "wamid.C"}]}
RATE_LIMITED = {"error": {"message": "Too many messages", "code": 130429}}


class TestWhatsAppCampaign(IntegrationTestCase):
	"""Sending, scheduling, retries, cancellation and counts."""

	def setUp(self):
		"""Create the account and an approved template."""
		self.account = make_account()
		self.template = make_template("test_campaign")

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def campaign(self, recipients, submit=True, **values):
		"""Create (and submit) a campaign; values override the defaults."""
		fields = {
			"doctype": "WhatsApp Campaign",
			"title": "Test campaign",
			"template": self.template,
			"recipient_source": "Numbers",
			"numbers": "\n".join(recipients),
		}
		fields.update(values)
		campaign = frappe.get_doc(fields).insert(ignore_permissions=True)
		if submit:
			campaign.submit()
		return frappe.get_doc("WhatsApp Campaign", campaign.name)

	def test_sends_to_all_and_completes(self):
		numbers = [random_number(), random_number()]
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			campaign = self.campaign(numbers + [f"+{numbers[0]}", "12"], common_values="Asha\nSO-1")
		self.assertEqual(request.call_count, 2)
		body = request.call_args.kwargs["json"]
		self.assertEqual(
			[p["text"] for p in body["template"]["components"][0]["parameters"]], ["Asha", "SO-1"]
		)
		self.assertEqual(
			(campaign.status, campaign.total_recipients, campaign.sent_count), ("Completed", 2, 2)
		)
		self.assertEqual(frappe.db.count("WhatsApp Message", {"campaign": campaign.name}), 2)

	def test_per_recipient_values_from_a_list(self):
		number = random_number()
		recipient_list = frappe.get_doc(
			{
				"doctype": "WhatsApp Recipient List",
				"list_name": f"Test {frappe.generate_hash(length=6)}",
				"recipients": [{"phone_number": number, "variables": "Ravi | SO-77"}],
			}
		).insert(ignore_permissions=True)
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			self.campaign(
				[],
				recipient_source="Recipient List",
				recipient_list=recipient_list.name,
				numbers=None,
				variable_mode="Per Recipient",
			)
		parameters = request.call_args.kwargs["json"]["template"]["components"][0]["parameters"]
		self.assertEqual([p["text"] for p in parameters], ["Ravi", "SO-77"])

	def test_rate_limited_message_is_retried(self):
		answers = [graph_response(RATE_LIMITED, 400), graph_response(OK)]
		with patch(REQUESTS, side_effect=answers), patch.object(campaign_sender, "sleep") as sleep:
			campaign = self.campaign([random_number()])
		sleep.assert_called_once_with(2)
		self.assertEqual(
			(campaign.status, campaign.failed_count, campaign.sent_count), ("Completed", 0, 1)
		)

	def test_failures_and_retry(self):
		error = {"error": {"message": "Not on WhatsApp", "code": 131026}}
		with patch(REQUESTS, return_value=graph_response(error, 400)):
			campaign = self.campaign([random_number()])
		self.assertEqual((campaign.status, campaign.failed_count), ("Partially Failed", 1))
		with patch(REQUESTS, return_value=graph_response(OK)):
			self.assertEqual(campaign_sender.retry_failed(campaign.name), 1)
		self.assertEqual(frappe.db.get_value("WhatsApp Campaign", campaign.name, "status"), "Completed")

	def test_opted_out_recipient_is_recorded(self):
		number = random_number()
		set_opted_out(number, True, self.account)
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			campaign = self.campaign([number, random_number()])
		self.assertEqual(
			(request.call_count, campaign.opted_out_count, campaign.status), (1, 1, "Completed")
		)

	def test_scheduled_campaign_starts_when_due(self):
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			campaign = self.campaign([random_number()], scheduled_at=add_to_date(now_datetime(), hours=1))
			self.assertEqual(campaign.status, "Scheduled")
			request.assert_not_called()
			frappe.db.set_value(
				"WhatsApp Campaign", campaign.name, "scheduled_at", add_to_date(now_datetime(), minutes=-1)
			)
			tasks.start_due_campaigns()
		self.assertEqual(frappe.db.get_value("WhatsApp Campaign", campaign.name, "status"), "Completed")

	def test_cancelled_campaign_stops(self):
		campaign = self.campaign([random_number()], scheduled_at=add_to_date(now_datetime(), hours=1))
		campaign.cancel()
		with patch(REQUESTS) as request:
			campaign_sender.send_batch(campaign.name, [{"phone_number": random_number()}])
		request.assert_not_called()
		self.assertEqual(frappe.db.get_value("WhatsApp Campaign", campaign.name, "status"), "Cancelled")

	def test_multi_product_and_catalog_buttons(self):
		template = make_template(
			"test_campaign_products",
			buttons=[
				{"button_type": "Multi-Product", "label": "View items"},
				{"button_type": "Catalog", "label": "View catalog"},
			],
		)
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			self.campaign([random_number()], template=template, product_ids="p1\np2", section_title="New")
		mpm, catalog = request.call_args.kwargs["json"]["template"]["components"][1:]
		self.assertEqual(
			mpm["parameters"][0]["action"],
			{
				"thumbnail_product_retailer_id": "p1",
				"sections": [
					{
						"title": "New",
						"product_items": [{"product_retailer_id": "p1"}, {"product_retailer_id": "p2"}],
					}
				],
			},
		)
		self.assertEqual(catalog["parameters"][0]["action"], {"thumbnail_product_retailer_id": "p1"})

	def test_validation(self):
		pending = make_template("test_campaign_pending", status="Pending")
		with self.assertRaises(frappe.ValidationError):
			self.campaign([random_number()], submit=False, template=pending)
		with self.assertRaises(frappe.ValidationError):
			self.campaign(["12"], submit=False)
		with self.assertRaises(frappe.ValidationError):
			self.campaign(
				[random_number()], submit=False, scheduled_at=add_to_date(now_datetime(), hours=-1)
			)
