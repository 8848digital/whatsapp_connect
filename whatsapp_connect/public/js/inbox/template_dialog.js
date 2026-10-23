// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

import { SEND_API } from "./constants";

const TEMPLATE_PREVIEW_API = "whatsapp_connect.whatsapp_connect_core.api.v1.template.preview";

/**
 * Open the dialog that sends an approved template, to the open conversation or to a new number.
 *
 * Each body variable gets an input. An empty input keeps the value from the
 * record the conversation belongs to, or the template's sample.
 *
 * @param {object} options - {phone_number, on_sent}; no phone_number asks for one.
 * @returns {object} The dialog.
 */
export function open_template_dialog(options) {
	const dialog = new frappe.ui.Dialog({
		title: options.phone_number ? __("Send a template") : __("New WhatsApp message"),
		fields: [
			{
				fieldname: "phone_number",
				label: __("Number"),
				fieldtype: "Data",
				options: "Phone",
				reqd: 1,
				default: options.phone_number,
				hidden: options.phone_number ? 1 : 0,
				description: __("With the country code, for example +91 99000 00101"),
			},
			{
				fieldname: "template",
				label: __("Template"),
				fieldtype: "Link",
				options: "WhatsApp Template",
				reqd: 1,
				get_query: () => ({ filters: { status: "Approved" } }),
				onchange: () => show_template(),
			},
			{ fieldname: "variables", fieldtype: "HTML" },
			{ fieldname: "preview", fieldtype: "HTML" },
		],
		primary_action_label: __("Send"),
		primary_action: (values) => send(values),
	});

	/** Draw an input for each body variable and the preview bubble. */
	function show_template() {
		const template = dialog.get_value("template");
		const $variables = dialog.fields_dict.variables.$wrapper.empty();
		const $preview = dialog.fields_dict.preview.$wrapper.empty();
		if (!template) return;

		frappe.db.get_value("WhatsApp Template", template, ["body", "body_samples"]).then((r) => {
			const body = (r.message && r.message.body) || "";
			const samples = ((r.message && r.message.body_samples) || "").split("\n");
			const count = new Set((body.match(/\{\{\d+\}\}/g) || []).map((match) => match)).size;
			const inputs = Array.from({ length: count }, (unused, index) => {
				const sample = frappe.utils.escape_html(samples[index] || "");
				return `<div class="form-group">
					<label class="control-label">{{${index + 1}}}</label>
					<input type="text" class="form-control wac-variable-input" data-index="${index}" placeholder="${sample}">
				</div>`;
			});
			$variables.html(inputs.join(""));
		});
		frappe
			.call({ method: TEMPLATE_PREVIEW_API, type: "GET", args: { template } })
			.then((r) => {
				const preview = (r.message && r.message.data) || {};
				$preview.html(
					whatsapp_connect.bubble({
						...preview,
						body_html: whatsapp_connect.format_text(preview.body),
					})
				);
			});
	}

	/** Send the template with the typed values. */
	function send(values) {
		const body_values = dialog.fields_dict.variables.$wrapper
			.find(".wac-variable-input")
			.toArray()
			.map((input) => input.value.trim());
		frappe.call({
			method: `${SEND_API}.send_template`,
			args: {
				phone_number: values.phone_number,
				template: values.template,
				body_values: JSON.stringify(body_values),
			},
			freeze: true,
			freeze_message: __("Sending..."),
			callback: (r) => {
				const result = r.message || {};
				frappe.show_alert({
					message: result.message,
					indicator: result.status ? "green" : "red",
				});
				if (!result.status) return;
				dialog.hide();
				if (options.on_sent) options.on_sent(result.data.phone_number);
			},
		});
	}

	dialog.show();
	return dialog;
}
