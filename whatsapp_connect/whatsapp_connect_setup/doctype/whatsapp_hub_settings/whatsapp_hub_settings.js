// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

const HUB_API = "/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub";

frappe.ui.form.on("WhatsApp Hub Settings", {
	/**
	 * Show the URLs to enter in the hub's Meta app.
	 *
	 * @param {object} frm - The WhatsApp Hub Settings form.
	 * @returns {void}
	 */
	refresh(frm) {
		const origin = window.location.origin;
		const row = (label, value) => `
			<div class="form-group">
				<div class="control-label">${label}</div>
				<div class="control-value like-disabled-input"><code>${frappe.utils.escape_html(
					value
				)}</code></div>
			</div>`;
		frm.fields_dict.hub_info.$wrapper.html(
			row(__("Webhook callback URL of the Meta app"), `${origin}${HUB_API}.webhook`) +
				row(__("Allowed domain for the JavaScript SDK"), window.location.host) +
				row(__("Hub URL for sites (WhatsApp Settings)"), origin) +
				`<p class="help-box small text-muted">${__(
					"Subscribe the webhook to messages, message_template_status_update and smb_message_echoes. See docs/hub-setup.md."
				)}</p>`
		);
	},
});
