# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe
from frappe.utils import add_to_date, now_datetime

from whatsapp_connect.tests.utils import IntegrationTestCase, make_account, random_number
from whatsapp_connect.whatsapp_connect_core.doctype.whatsapp_profile.profile_utils import (
	record_incoming,
)
from whatsapp_connect.whatsapp_connect_core.messaging.opt_out import (
	apply_keyword,
	filter_opted_out,
	is_opted_out,
)
from whatsapp_connect.whatsapp_connect_core.messaging.reply_window import is_window_open


class TestWhatsAppProfile(IntegrationTestCase):
	"""Profiles, opt-out keywords and the 24-hour reply window."""

	def setUp(self):
		"""Create the test account and a fresh number."""
		self.account = make_account()
		self.number = random_number()

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_number_is_normalized(self):
		profile = frappe.get_doc(
			{"doctype": "WhatsApp Profile", "phone_number": f"+{self.number[:2]} {self.number[2:]}"}
		).insert(ignore_permissions=True)
		self.assertEqual(profile.name, self.number)

	def test_stop_and_start(self):
		self.assertEqual(apply_keyword(self.number, " Stop! ", self.account), "opted_out")
		self.assertTrue(is_opted_out("+" + self.number))
		self.assertEqual(apply_keyword(self.number, "START", self.account), "opted_in")
		self.assertFalse(is_opted_out(self.number))

	def test_other_text_is_not_a_keyword(self):
		self.assertIsNone(apply_keyword(self.number, "please stop the order", self.account))
		self.assertFalse(is_opted_out(self.number))

	def test_filter_opted_out(self):
		apply_keyword(self.number, "stop", self.account)
		other = random_number()
		self.assertEqual(filter_opted_out([other, "+" + self.number]), ([other], ["+" + self.number]))

	def test_reply_window(self):
		self.assertFalse(is_window_open(self.number))
		record_incoming(self.number, "Asha", self.account, now_datetime())
		self.assertTrue(is_window_open(self.number))
		self.assertEqual(frappe.db.get_value("WhatsApp Profile", self.number, "profile_name"), "Asha")
		record_incoming(self.number, None, self.account, add_to_date(now_datetime(), hours=-25))
		self.assertFalse(is_window_open(self.number))
