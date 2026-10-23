// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

const TEMPLATE_API = "whatsapp_connect.whatsapp_connect_core.api.v1.template";
const PREVIEW_FIELDS = [
	"body",
	"body_samples",
	"header_type",
	"header_text",
	"header_sample",
	"footer",
];

frappe.ui.form.on("WhatsApp Template", {
	/**
	 * Show the preview and the Submit to Meta button.
	 *
	 * @param {object} frm - The WhatsApp Template form.
	 * @returns {void}
	 */
	refresh(frm) {
		render_template_preview(frm);
		if (!frm.is_new()) {
			const label = frm.doc.meta_template_id ? __("Update in Meta") : __("Submit to Meta");
			frm.add_custom_button(label, () => {
				frappe.call({
					method: `${TEMPLATE_API}.submit`,
					args: { template: frm.doc.name },
					freeze: true,
					freeze_message: __("Sending to Meta..."),
					callback: (r) => {
						if (r.message)
							frappe.show_alert({ message: r.message.message, indicator: "green" });
						frm.reload_doc();
					},
				});
			});
		}
	},
	buttons_remove: render_template_preview,
	...Object.fromEntries(PREVIEW_FIELDS.map((field) => [field, render_template_preview])),
});

frappe.ui.form.on("WhatsApp Template Button", {
	label: render_template_preview,
	button_type: render_template_preview,
});

/**
 * Draw the template as WhatsApp shows it, with the samples in place of the variables.
 *
 * @param {object} frm - The WhatsApp Template form.
 * @returns {void}
 */
function render_template_preview(frm) {
	const field = frm.fields_dict.preview;
	if (!field) return;
	const samples = (frm.doc.body_samples || "").split("\n").map((line) => line.trim());
	const body = frm.doc.body || __("Type the template text to see the preview.");
	const header = (frm.doc.header_text || "").replace("{{1}}", frm.doc.header_sample || "{{1}}");
	field.$wrapper.html(
		whatsapp_connect.bubble({
			header,
			header_type: frm.doc.header_type,
			body_html: whatsapp_connect.format_text(body, samples),
			footer: frm.doc.footer,
			buttons: (frm.doc.buttons || []).map((button) => button.label).filter(Boolean),
		})
	);
}
