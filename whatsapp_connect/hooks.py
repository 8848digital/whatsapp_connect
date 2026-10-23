# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Hook registration for WhatsApp Connect. No business logic here."""

app_name = "whatsapp_connect"
app_title = "WhatsApp Connect"
app_publisher = "8848 Digital LLP"
app_description = "WhatsApp Business messaging for Frappe and ERPNext through the Meta Cloud API"
app_email = "satya@8848digital.com"
app_license = "mit"

custom_fixtures = [
	{
		"dt": "Custom Field",
		"filters": {
			"module": [
				"in",
				[
					"WhatsApp Connect Core",
					"WhatsApp Connect Notification",
					"WhatsApp Connect Campaign",
					"WhatsApp Connect Flow",
				],
			]
		},
	}
]

commands = ["whatsapp_connect.commands.export_fixtures.export_fixtures"]

# after_request is not wired: the webhook verification and the Flow endpoint
# must answer Meta in plain text, which the response formatter would try to
# parse as JSON. Endpoints call utils.api_handlers.envelope.api_response.
