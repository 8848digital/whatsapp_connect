# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Hook registration for WhatsApp Connect. No business logic here."""

app_name = "whatsapp_connect"
app_title = "WhatsApp Connect"
app_publisher = "8848 Digital LLP"
app_description = "WhatsApp Business messaging for Frappe and ERPNext through the Meta Cloud API"
app_email = "satya@8848digital.com"
app_license = "mit"
app_logo_url = "/assets/whatsapp_connect/images/logo.svg"

# Apps screen (Frappe 15+).
add_to_apps_screen = [
	{
		"name": "whatsapp_connect",
		"logo": "/assets/whatsapp_connect/images/logo.svg",
		"title": "WhatsApp Connect",
		"route": "/app/whatsapp-inbox",
	}
]

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
					"WhatsApp Connect Setup",
				],
			]
		},
	}
]

commands = ["whatsapp_connect.commands.export_fixtures.export_fixtures"]

app_include_js = "whatsapp_connect.bundle.js"
app_include_css = "/assets/whatsapp_connect/css/whatsapp_connect.css"

before_install = "whatsapp_connect.install.before_install"

_NOTIFICATION_TASKS = "whatsapp_connect.whatsapp_connect_notification.tasks"

scheduler_events = {
	"all": ["whatsapp_connect.whatsapp_connect_campaign.tasks.start_due_campaigns"],
	"hourly": [
		f"{_NOTIFICATION_TASKS}.run_hourly",
		"whatsapp_connect.whatsapp_connect_campaign.tasks.refresh_running_campaigns",
	],
	"daily": [
		"whatsapp_connect.whatsapp_connect_core.tasks.clear_old_logs",
		f"{_NOTIFICATION_TASKS}.run_daily",
		"whatsapp_connect.whatsapp_connect_setup.hub.tasks.delete_stale_sessions",
	],
	"weekly": [f"{_NOTIFICATION_TASKS}.run_weekly"],
	"monthly": [f"{_NOTIFICATION_TASKS}.run_monthly"],
	"yearly": [f"{_NOTIFICATION_TASKS}.run_yearly"],
}

# WhatsApp Notifications on any doctype (whatsapp_connect_notification/notification_events.py).
_NOTIFICATION_EVENT = (
	"whatsapp_connect.whatsapp_connect_notification.notification_events.handle_event"
)
doc_events = {
	"*": {
		event: _NOTIFICATION_EVENT
		for event in (
			"after_insert",
			"on_update",
			"on_submit",
			"on_cancel",
			"on_trash",
			"on_update_after_submit",
		)
	}
}

# WhatsApp messages as cards in the timeline of the document they belong to.
additional_timeline_content = {
	"*": ["whatsapp_connect.whatsapp_connect_core.messaging.timeline.get_timeline_content"],
}

# Extension points between modules (see messaging/payload.py and webhook/handler.py):
# whatsapp_connect_payload_builders = {"<message_type>": "<dotted.path>"}
# whatsapp_connect_webhook_fields = {"<webhook field>": "<dotted.path>"}
whatsapp_connect_payload_builders = {
	"template": "whatsapp_connect.whatsapp_connect_core.messaging.template_payload.build_template_object",
	"flow": "whatsapp_connect.whatsapp_connect_flow.sending.build_flow_object",
}
# Called with each saved incoming WhatsApp Message.
whatsapp_connect_incoming_handlers = [
	"whatsapp_connect.whatsapp_connect_core.messaging.lead_capture.handle_incoming",
	"whatsapp_connect.whatsapp_connect_flow.responses.handle_incoming",
	"whatsapp_connect.whatsapp_connect_inbox.notifications.handle_incoming",
]

# after_request is not wired: the webhook verification and the Flow endpoint
# must answer Meta in plain text, which the response formatter would try to
# parse as JSON. Endpoints call utils.api_handlers.envelope.api_response.
