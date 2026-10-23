// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.listview_settings["WhatsApp Template"] = {
	/**
	 * Add Sync from Meta to the list view.
	 *
	 * @param {object} listview - The WhatsApp Template list view.
	 * @returns {void}
	 */
	onload(listview) {
		listview.page.add_inner_button(__("Sync from Meta"), () => {
			frappe.prompt(
				[
					{
						fieldname: "account",
						label: __("WhatsApp Account"),
						fieldtype: "Link",
						options: "WhatsApp Account",
						reqd: 1,
					},
				],
				(values) => {
					frappe.call({
						method: "whatsapp_connect.whatsapp_connect_core.api.v1.template.sync",
						args: { account: values.account },
						freeze: true,
						freeze_message: __("Reading templates from Meta..."),
						callback: (r) => {
							if (r.message)
								frappe.show_alert({
									message: r.message.message,
									indicator: "green",
								});
							listview.refresh();
						},
					});
				},
				__("Sync from Meta"),
				__("Sync")
			);
		});
	},
	/**
	 * Colour the status indicator.
	 *
	 * @param {object} doc - A list row.
	 * @returns {string[]} [label, colour, filter].
	 */
	get_indicator(doc) {
		const colours = {
			Approved: "green",
			Pending: "orange",
			Rejected: "red",
			Paused: "yellow",
			Disabled: "gray",
			Draft: "gray",
		};
		return [__(doc.status), colours[doc.status] || "blue", `status,=,${doc.status}`];
	},
};
