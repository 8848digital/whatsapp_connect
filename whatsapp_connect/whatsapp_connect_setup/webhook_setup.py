# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Point Meta's webhooks to this site without the Meta App Dashboard."""

import frappe
from frappe import _

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI, CloudAPIError
from whatsapp_connect.whatsapp_connect_setup.graph import WEBHOOK_PATH, app_graph

WEBHOOK_FIELDS = ["messages", "message_template_status_update", "smb_message_echoes"]
# Fields that every app can subscribe to; smb_message_echoes needs coexistence access.
REQUIRED_FIELDS = WEBHOOK_FIELDS[:2]


def subscribe_webhooks(account: str) -> str:
	"""
	Make Meta send the account's webhooks to this site.

	Embedded Signup accounts receive webhooks through the hub, so only the app
	subscription of the business account is renewed. For an own Meta app, the
	app's webhook is set to this site first.

	Parameters:
	        account (str, required): The WhatsApp Account name.

	Returns:
	        str: What was done.
	"""
	doc = frappe.get_doc("WhatsApp Account", account)
	if doc.setup_method == "Embedded Signup":
		CloudAPI(doc).subscribe_app()
		return _("Webhooks come through the WhatsApp hub")
	app_secret = doc.get_password("app_secret", raise_exception=False)
	if not (doc.app_id and app_secret):
		frappe.throw(_("Enter the App ID and App Secret of the Meta app on the WhatsApp Account"))
	url = webhook_url()
	set_app_webhook(doc, app_secret, url)
	CloudAPI(doc).subscribe_app()
	return _("Meta sends webhooks to {0}").format(url)


def webhook_url() -> str:
	"""
	Return this site's webhook URL, and check that Meta can call it.

	Returns:
	        str: The callback URL.
	"""
	url = frappe.utils.get_url(WEBHOOK_PATH)
	if not url.startswith("https://") or "localhost" in url or "127.0.0.1" in url:
		frappe.throw(
			_(
				"Meta can only call a site on the internet over https://. This site's URL is {0}. Set host_name in the site config to the public URL."
			).format(url)
		)
	return url


def set_app_webhook(doc, app_secret: str, url: str) -> None:
	"""
	Set the Meta app's WhatsApp webhook (callback URL, verify token and fields).

	Meta calls the URL with the verify token before it answers, so the account
	must be saved and committed first.

	Parameters:
	        doc (Document, required): The WhatsApp Account.
	        app_secret (str, required): The Meta App Secret.
	        url (str, required): The callback URL.

	Returns:
	        None
	"""
	graph = app_graph(doc.app_id, app_secret, doc)
	body = {
		"object": "whatsapp_business_account",
		"callback_url": url,
		"verify_token": doc.verify_token,
		"include_values": "true",
	}
	path = f"{doc.app_id}/subscriptions"
	try:
		graph.request("POST", path, data={**body, "fields": ",".join(WEBHOOK_FIELDS)}, log_body=False)
	except CloudAPIError:
		try:
			graph.request("POST", path, data={**body, "fields": ",".join(REQUIRED_FIELDS)}, log_body=False)
		except CloudAPIError as exc:
			frappe.throw(
				_(
					"Meta could not set the webhook to {0}: {1}. Check that the site is reachable from the internet."
				).format(url, exc.describe())
			)
