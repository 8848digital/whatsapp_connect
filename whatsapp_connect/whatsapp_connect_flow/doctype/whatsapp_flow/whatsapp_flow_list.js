// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.listview_settings["WhatsApp Flow"] = {
	/**
	 * Add Import from Meta to the list view.
	 *
	 * @param {object} listview - The WhatsApp Flow list view.
	 * @returns {void}
	 */
	onload(listview) {
		listview.page.add_inner_button(__("Import from Meta"), () => {
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
				(values) =>
					frappe.call({
						method: "whatsapp_connect.whatsapp_connect_flow.api.v1.flow.import_flows",
						args: { account: values.account },
						freeze: true,
						callback: (r) => {
							if (r.message)
								frappe.show_alert({
									message: r.message.message,
									indicator: "green",
								});
							listview.refresh();
						},
					}),
				__("Import from Meta"),
				__("Import")
			);
		});
	},
};
