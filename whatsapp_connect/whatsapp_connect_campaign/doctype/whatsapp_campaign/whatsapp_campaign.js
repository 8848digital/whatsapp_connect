// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

const CAMPAIGN_API = "whatsapp_connect.whatsapp_connect_campaign.api.v1.campaign";

frappe.ui.form.on("WhatsApp Campaign", {
	/**
	 * Only approved templates can be used.
	 *
	 * @param {object} frm - The WhatsApp Campaign form.
	 * @returns {void}
	 */
	setup(frm) {
		frm.set_query("template", () => ({ filters: { status: "Approved" } }));
	},
	/**
	 * Show the progress and the Refresh and Retry Failed buttons on submitted campaigns.
	 *
	 * @param {object} frm - The WhatsApp Campaign form.
	 * @returns {void}
	 */
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;
		show_progress(frm);
		frm.add_custom_button(__("Refresh Progress"), () => call_campaign_api(frm, "refresh"));
		if (frm.doc.failed_count) {
			frm.add_custom_button(__("Retry Failed"), () =>
				call_campaign_api(frm, "retry_failed")
			);
		}
	},
});

/**
 * Show a progress bar of sent, delivered and read messages.
 *
 * @param {object} frm - The WhatsApp Campaign form.
 * @returns {void}
 */
function show_progress(frm) {
	const total = frm.doc.total_recipients || 0;
	if (!total) return;
	const read = frm.doc.read_count || 0;
	frm.dashboard.show_progress(
		__("Read"),
		(read * 100) / total,
		__("{0} of {1} read · {2} delivered · {3} sent · {4} failed · {5} opted out", [
			read,
			total,
			frm.doc.delivered_count || 0,
			frm.doc.sent_count || 0,
			frm.doc.failed_count || 0,
			frm.doc.opted_out_count || 0,
		])
	);
}

/**
 * Call a campaign endpoint and reload the form.
 *
 * @param {object} frm - The WhatsApp Campaign form.
 * @param {string} endpoint - Function name in api/v1/campaign.py.
 * @returns {void}
 */
function call_campaign_api(frm, endpoint) {
	frappe.call({
		method: `${CAMPAIGN_API}.${endpoint}`,
		args: { campaign: frm.doc.name },
		freeze: true,
		callback: (r) => {
			if (r.message && r.message.message)
				frappe.show_alert({ message: r.message.message, indicator: "green" });
			frm.reload_doc();
		},
	});
}
