// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.ui.form.on("WhatsApp Account", {
	/**
	 * Show how webhooks reach the site and add the account buttons.
	 *
	 * @param {object} frm - The WhatsApp Account form.
	 * @returns {void}
	 */
	refresh(frm) {
		frm.add_custom_button(__("WhatsApp Setup"), () => frappe.set_route("whatsapp-setup"));
		if (frm.doc.setup_method === "Embedded Signup") {
			frm.fields_dict.webhook_info.$wrapper.html(
				`<p class="help-box small text-muted">${__(
					"Connected with Facebook: webhooks come through the WhatsApp hub, nothing to set in Meta."
				)}</p>`
			);
			if (frm.doc.hub_connection) {
				frm.add_custom_button(__("Disconnect from Hub"), () => {
					frappe.confirm(
						__("Stop receiving webhooks for this number and disable the account?"),
						() =>
							frappe
								.call({
									method: "whatsapp_connect.whatsapp_connect_setup.api.v1.setup.disconnect_hub",
									args: { account: frm.doc.name },
									freeze: true,
								})
								.then(() => frm.reload_doc())
					);
				});
			}
		} else {
			frm.events.show_webhook_url(frm);
		}
		frm.events.add_account_buttons(frm);
	},

	/**
	 * Show the callback URL to enter in Meta for an own Meta app.
	 *
	 * @param {object} frm - The WhatsApp Account form.
	 * @returns {void}
	 */
	show_webhook_url(frm) {
		const url = `${window.location.origin}/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.webhook.receive`;
		frm.fields_dict.webhook_info.$wrapper.html(`
			<div class="form-group">
				<div class="control-label">${__("Callback URL for Meta")}</div>
				<div class="control-value like-disabled-input"><code>${frappe.utils.escape_html(url)}</code></div>
				<p class="help-box small text-muted">${__(
					"In Meta: WhatsApp > Configuration > Webhook. Subscribe to messages, message_template_status_update and smb_message_echoes."
				)}</p>
			</div>`);
	},

	/**
	 * Add the Flow keys and webhook subscription buttons to a saved account.
	 *
	 * @param {object} frm - The WhatsApp Account form.
	 * @returns {void}
	 */
	add_account_buttons(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Generate Flow Keys"), () => {
				frappe.confirm(
					__("Create a new key pair for WhatsApp Flows and register it in Meta?"),
					() =>
						frappe.call({
							method: "whatsapp_connect.whatsapp_connect_flow.api.v1.flow.generate_keys",
							args: { account: frm.doc.name },
							freeze: true,
							callback: (r) => {
								if (r.message)
									frappe.show_alert({
										message: r.message.message,
										indicator: "green",
									});
								frm.reload_doc();
							},
						})
				);
			});
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
