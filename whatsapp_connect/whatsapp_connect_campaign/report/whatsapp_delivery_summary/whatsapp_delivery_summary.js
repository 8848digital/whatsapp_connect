// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.query_reports["WhatsApp Delivery Summary"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: ["Template", "Campaign", "WhatsApp Account", "Day"],
			default: "Template",
		},
		{
			fieldname: "whatsapp_account",
			label: __("WhatsApp Account"),
			fieldtype: "Link",
			options: "WhatsApp Account",
		},
	],
};
