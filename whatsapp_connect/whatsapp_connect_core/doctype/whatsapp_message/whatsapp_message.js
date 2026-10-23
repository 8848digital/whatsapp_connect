// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

const MESSAGE_API = "whatsapp_connect.whatsapp_connect_core.api.v1.message";

frappe.ui.form.on("WhatsApp Message", {
	/**
	 * Add Retry for failed messages and Mark as Read for received ones.
	 *
	 * @param {object} frm - The WhatsApp Message form.
	 * @returns {void}
	 */
	refresh(frm) {
		if (frm.doc.direction === "Outgoing" && frm.doc.status === "Failed") {
			frm.add_custom_button(__("Send Again"), () => call_message_api(frm, "retry"));
		}
		if (frm.doc.direction === "Incoming" && frm.doc.wamid) {
			frm.add_custom_button(__("Mark as Read"), () => call_message_api(frm, "mark_as_read"));
		}
	},
});

/**
 * Call a message endpoint and reload the form.
 *
 * @param {object} frm - The WhatsApp Message form.
 * @param {string} endpoint - Function name in api/v1/message.py.
 * @returns {void}
 */
function call_message_api(frm, endpoint) {
	frappe.call({
		method: `${MESSAGE_API}.${endpoint}`,
		args: { message: frm.doc.name },
		freeze: true,
		callback: (r) => {
			if (r.message) frappe.show_alert({ message: r.message.message, indicator: "green" });
			frm.reload_doc();
		},
	});
}
