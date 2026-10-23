// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.ui.form.on("WhatsApp Recipient List", {
	/**
	 * Add the Import Recipients button.
	 *
	 * @param {object} frm - The WhatsApp Recipient List form.
	 * @returns {void}
	 */
	refresh(frm) {
		if (frm.is_new() || !frm.doc.source_doctype) return;
		frm.add_custom_button(__("Import Recipients"), () => {
			frappe.call({
				method: "whatsapp_connect.whatsapp_connect_campaign.api.v1.recipient_list.import_recipients",
				args: { recipient_list: frm.doc.name },
				freeze: true,
				callback: (r) => {
					if (r.message)
						frappe.show_alert({ message: r.message.message, indicator: "green" });
					frm.reload_doc();
				},
			});
		});
	},
});
