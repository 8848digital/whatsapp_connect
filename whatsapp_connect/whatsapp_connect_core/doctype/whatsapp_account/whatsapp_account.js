// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.ui.form.on("WhatsApp Account", {
	/**
	 * Show the webhook URL and add the Subscribe button.
	 *
	 * @param {object} frm - The WhatsApp Account form.
	 * @returns {void}
	 */
	refresh(frm) {
		const url = `${window.location.origin}/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.webhook.receive`;
		frm.fields_dict.webhook_info.$wrapper.html(`
			<div class="form-group">
				<div class="control-label">${__("Callback URL for Meta")}</div>
				<div class="control-value like-disabled-input"><code>${frappe.utils.escape_html(url)}</code></div>
				<p class="help-box small text-muted">${__(
					"In Meta: WhatsApp > Configuration > Webhook. Subscribe to messages, message_template_status_update and smb_message_echoes."
				)}</p>
			</div>`);

		if (!frm.is_new()) {
			frm.add_custom_button(__("Subscribe App to Webhooks"), () => {
				frappe.call({
					method: "whatsapp_connect.whatsapp_connect_core.api.v1.account.subscribe_app",
					args: { account: frm.doc.name },
					freeze: true,
					callback: (r) => {
						if (r.message && r.message.status) {
							frappe.show_alert({ message: r.message.message, indicator: "green" });
						}
					},
				});
			});
		}
	},
});
