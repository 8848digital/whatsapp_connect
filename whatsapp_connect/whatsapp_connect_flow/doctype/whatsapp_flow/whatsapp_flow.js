// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

const FLOW_API = "whatsapp_connect.whatsapp_connect_flow.api.v1.flow";

frappe.ui.form.on("WhatsApp Flow", {
	/**
	 * Add the Meta actions that fit the flow's status.
	 *
	 * @param {object} frm - The WhatsApp Flow form.
	 * @returns {void}
	 */
	refresh(frm) {
		if (frm.is_new()) return;
		const meta = __("Meta");
		if (frm.doc.status === "Draft") {
			frm.add_custom_button(
				__("Save to Meta"),
				() => call_flow_api(frm, "save_to_meta"),
				meta
			);
		}
		if (frm.doc.meta_flow_id) {
			if (frm.doc.status === "Draft")
				frm.add_custom_button(__("Publish"), () => confirm_publish(frm), meta);
			if (frm.doc.status === "Published")
				frm.add_custom_button(
					__("Deprecate"),
					() => call_flow_api(frm, "deprecate"),
					meta
				);
			frm.add_custom_button(
				__("Refresh Status"),
				() => call_flow_api(frm, "refresh_status"),
				meta
			);
			frm.add_custom_button(__("Send to a Number"), () => send_flow(frm));
		}
		if (frm.doc.preview_url) {
			frm.add_custom_button(__("Open Preview"), () =>
				window.open(frm.doc.preview_url, "_blank")
			);
		}
	},
});

/**
 * Call a flow endpoint and reload the form.
 *
 * @param {object} frm - The WhatsApp Flow form.
 * @param {string} endpoint - Function name in api/v1/flow.py.
 * @param {object} [args] - Extra arguments.
 * @returns {void}
 */
function call_flow_api(frm, endpoint, args = {}) {
	frappe.call({
		method: `${FLOW_API}.${endpoint}`,
		args: { flow: frm.doc.name, ...args },
		freeze: true,
		callback: (r) => {
			const result = r.message || {};
			if (result.message)
				frappe.show_alert({
					message: result.message,
					indicator: result.status === false ? "orange" : "green",
				});
			frm.reload_doc();
		},
	});
}

/**
 * Ask before publishing: a published flow cannot be changed.
 *
 * @param {object} frm - The WhatsApp Flow form.
 * @returns {void}
 */
function confirm_publish(frm) {
	frappe.confirm(__("A published flow cannot be changed any more. Publish it?"), () =>
		call_flow_api(frm, "publish")
	);
}

/**
 * Ask for a number and send the flow to it.
 *
 * @param {object} frm - The WhatsApp Flow form.
 * @returns {void}
 */
function send_flow(frm) {
	frappe.prompt(
		[
			{ fieldname: "to", label: __("Phone Number"), fieldtype: "Data", reqd: 1 },
			{
				fieldname: "text",
				label: __("Text"),
				fieldtype: "Small Text",
				default: frm.doc.flow_name,
			},
		],
		(values) => call_flow_api(frm, "send", values),
		__("Send Flow"),
		__("Send")
	);
}
