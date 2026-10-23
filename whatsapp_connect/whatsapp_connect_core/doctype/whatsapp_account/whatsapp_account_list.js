// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.listview_settings["WhatsApp Account"] = {
	/**
	 * Add the WhatsApp Setup button, the easy way to connect a number.
	 *
	 * @param {object} listview - The list view.
	 * @returns {void}
	 */
	onload(listview) {
		listview.page.add_inner_button(__("WhatsApp Setup"), () =>
			frappe.set_route("whatsapp-setup")
		);
	},
};
