# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from datetime import datetime
from unittest.mock import patch

import frappe

from whatsapp_connect.tests.utils import IntegrationTestCase
from whatsapp_connect.whatsapp_connect_automation.business_hours import is_open

ROWS = "whatsapp_connect.whatsapp_connect_automation.business_hours.frappe.get_all"
# 2026-10-26 is a Monday.
MONDAY_NOON = datetime(2026, 10, 26, 12, 0)
MONDAY_NIGHT = datetime(2026, 10, 26, 21, 0)
SUNDAY_NOON = datetime(2026, 10, 25, 12, 0)


class TestBusinessHours(IntegrationTestCase):
	"""Open and closed times of WhatsApp Auto Reply Settings."""

	def test_hours_of_the_day(self):
		rows = [frappe._dict(day="Monday", opens_at="09:00:00", closes_at="18:00:00")]
		with patch(ROWS, return_value=rows):
			self.assertTrue(is_open(MONDAY_NOON))
			self.assertFalse(is_open(MONDAY_NIGHT))
			# A day without a row is closed.
			self.assertFalse(is_open(SUNDAY_NOON))

	def test_no_hours_means_always_open(self):
		with patch(ROWS, return_value=[]):
			self.assertTrue(is_open(SUNDAY_NOON))
