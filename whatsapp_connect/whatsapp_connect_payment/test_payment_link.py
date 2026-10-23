# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe

from whatsapp_connect.tests.utils import (
	REQUESTS,
	IntegrationTestCase,
	graph_response,
	make_account,
	make_template,
	random_number,
)
from whatsapp_connect.whatsapp_connect_core.messaging.template_preview import render_preview
from whatsapp_connect.whatsapp_connect_core.messaging.template_send import send_template
from whatsapp_connect.whatsapp_connect_payment import payment_link
from whatsapp_connect.www import whatsapp_pay

MODULE = "whatsapp_connect.whatsapp_connect_payment.payment_link"
REQUEST = frappe._dict(
	name="ACC-PRQ-TEST-0001", payment_url="https://pay.example.com/checkout/abc"
)
OK = {"messages": [{"id": "wamid.PAY"}]}


class TestPaymentLink(IntegrationTestCase):
	"""Payment links in templates and the /whatsapp_pay page."""

	def setUp(self):
		"""Use a contact as the document; the Payment Request is patched."""
		self.account = make_account()
		self.number = random_number()
		self.contact = frappe.get_doc({"doctype": "Contact", "first_name": "Karan"}).insert(
			ignore_permissions=True
		)
		self.request_patcher = patch(f"{MODULE}.get_payment_request", return_value=REQUEST)
		self.get_request = self.request_patcher.start()
		self.addCleanup(self.request_patcher.stop)

	def tearDown(self):
		"""Undo the test's database changes."""
		frappe.db.rollback()

	def test_payment_link_fills_a_body_variable(self):
		template = make_template(
			"test_pay_link", account=self.account, body_fields="first_name\npayment_link"
		)
		with patch(REQUESTS, return_value=graph_response(OK)) as request:
			send_template(template, self.number, doc=self.contact)
		parameters = request.call_args.kwargs["json"]["template"]["components"][0]["parameters"]
		self.assertEqual([p["text"] for p in parameters], ["Karan", REQUEST.payment_url])

	def test_preview_makes_no_payment_request(self):
		template = make_template(
			"test_pay_preview", account=self.account, body_fields="first_name\npayment_link"
		)
		preview = render_preview(template, "Contact", self.contact.name)
		self.assertIn("(payment link)", preview["body"])
		self.get_request.assert_not_called()

	def test_token_opens_the_payment_url(self):
		token = payment_link.payment_link_token(self.contact)
		self.assertTrue(token.startswith(f"{REQUEST.name}~"))
		open_request = frappe._dict(payment_url=REQUEST.payment_url, status="Requested")
		with patch(f"{MODULE}.frappe.db.get_value", return_value=open_request):
			self.assertEqual(payment_link.resolve_token(token), REQUEST.payment_url)
			tampered = token[:-1] + ("1" if token[-1] == "0" else "0")
			self.assertIsNone(payment_link.resolve_token(tampered))
			self.assertIsNone(payment_link.resolve_token("ACC-PRQ-TEST-0002~" + token.split("~")[1]))

		paid_request = frappe._dict(payment_url=REQUEST.payment_url, status="Paid")
		with patch(f"{MODULE}.frappe.db.get_value", return_value=paid_request):
			self.assertIsNone(payment_link.resolve_token(token))

	def test_pay_page_redirects_or_explains(self):
		token = payment_link.payment_link_token(self.contact)
		with patch.object(whatsapp_pay, "resolve_token", return_value=REQUEST.payment_url):
			frappe.form_dict.t = token
			with self.assertRaises(frappe.Redirect):
				whatsapp_pay.get_context(frappe._dict())
			self.assertEqual(frappe.local.flags.redirect_location, REQUEST.payment_url)

		frappe.form_dict.t = "bad"
		context = whatsapp_pay.get_context(frappe._dict())
		self.assertIn("not valid", context.message)

	def test_only_payable_documents(self):
		self.request_patcher.stop()
		with self.assertRaises(frappe.ValidationError):
			payment_link.get_payment_request(self.contact)
