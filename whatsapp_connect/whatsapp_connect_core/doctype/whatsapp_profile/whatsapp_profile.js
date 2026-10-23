// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.ui.form.on("WhatsApp Profile", {
	/**
	 * Add Open in Inbox, which opens this number's conversation.
	 *
	 * @param {object} frm - The form.
	 * @returns {void}
	 */
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Open in Inbox"), () =>
			frappe.set_route("whatsapp-inbox", frm.doc.name)
		);
	},
});
