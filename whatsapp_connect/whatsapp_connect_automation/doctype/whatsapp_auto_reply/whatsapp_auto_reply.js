// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.ui.form.on("WhatsApp Auto Reply", {
	/**
	 * Offer the registered actions in the Action field.
	 *
	 * @param {object} frm - The form.
	 * @returns {void}
	 */
	onload(frm) {
		frappe
			.call({
				method: "whatsapp_connect.whatsapp_connect_automation.api.v1.auto_reply.get_actions",
				type: "GET",
			})
			.then((r) => {
				const actions = (r.message && r.message.data) || [];
				// Keep a saved action that is no longer registered, so the form shows it.
				if (frm.doc.action && !actions.includes(frm.doc.action))
					actions.push(frm.doc.action);
				frm.set_df_property("action", "options", ["", ...actions]);
			});
	},
});
