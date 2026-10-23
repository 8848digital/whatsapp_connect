// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

const FIELD_SELECTS = {
	phone_field: (df) => ["Data", "Phone"].includes(df.fieldtype),
	value_changed: (df) => !frappe.model.no_value_type.includes(df.fieldtype),
	date_field: (df) => ["Date", "Datetime"].includes(df.fieldtype),
	attach_from_field: (df) => ["Attach", "Attach Image"].includes(df.fieldtype),
	set_field: (df) => !frappe.model.no_value_type.includes(df.fieldtype) && !df.read_only,
};

frappe.ui.form.on("WhatsApp Notification", {
	/**
	 * Limit print formats and templates, and add Send Now.
	 *
	 * @param {object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	setup(frm) {
		frm.set_query("print_format", () => ({
			filters: { doc_type: frm.doc.reference_doctype },
		}));
		frm.set_query("template", () => ({ filters: { status: "Approved" } }));
	},
	/**
	 * Fill the field lists and add the Send Now button.
	 *
	 * @param {object} frm - The WhatsApp Notification form.
	 * @returns {void}
	 */
	refresh(frm) {
		fill_field_selects(frm);
		if (!frm.is_new()) {
			frm.add_custom_button(__("Send Now"), () => send_now(frm));
		}
	},
	reference_doctype: fill_field_selects,
});

/**
 * Offer the document type's fields in the field selects.
 *
 * @param {object} frm - The WhatsApp Notification form.
 * @returns {void}
 */
function fill_field_selects(frm) {
	if (!frm.doc.reference_doctype) return;
	frappe.model.with_doctype(frm.doc.reference_doctype, () => {
		const fields = frappe.get_meta(frm.doc.reference_doctype).fields;
		Object.entries(FIELD_SELECTS).forEach(([fieldname, accepts]) => {
			const options = fields
				.filter(accepts)
				.map((df) => ({
					value: df.fieldname,
					label: `${__(df.label || df.fieldname)} (${df.fieldname})`,
				}));
			frm.set_df_property(fieldname, "options", [{ value: "", label: "" }, ...options]);
		});
	});
}

/**
 * Ask for a document (when the notification has a document type) and send now.
 *
 * @param {object} frm - The WhatsApp Notification form.
 * @returns {void}
 */
function send_now(frm) {
	const call = (docname) =>
		frappe.call({
			method: "whatsapp_connect.whatsapp_connect_notification.api.v1.notification.send_now",
			args: { notification: frm.doc.name, docname },
			freeze: true,
			callback: (r) =>
				r.message && frappe.show_alert({ message: r.message.message, indicator: "green" }),
		});
	if (!frm.doc.reference_doctype) return call(null);
	frappe.prompt(
		[
			{
				fieldname: "docname",
				label: __(frm.doc.reference_doctype),
				fieldtype: "Link",
				options: frm.doc.reference_doctype,
				reqd: 1,
			},
		],
		(values) => call(values.docname),
		__("Send Now"),
		__("Send")
	);
}
