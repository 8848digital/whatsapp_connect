// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.query_reports["WhatsApp Campaign Recipients"] = {
	filters: [
		{
			fieldname: "campaign",
			label: __("Campaign"),
			fieldtype: "Link",
			options: "WhatsApp Campaign",
			reqd: 1,
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Queued", "Sent", "Delivered", "Read", "Failed", "Opted Out"],
		},
	],
};
