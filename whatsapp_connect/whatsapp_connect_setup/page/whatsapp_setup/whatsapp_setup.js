// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

const SETUP_API = "whatsapp_connect.whatsapp_connect_setup.api.v1.setup";

frappe.pages["whatsapp-setup"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("WhatsApp Setup"),
		single_column: true,
	});
	frappe.require("/assets/whatsapp_connect/js/whatsapp_setup_dialogs.js", () => {
		wrapper.whatsapp_setup = new WhatsAppSetupPage(page);
	});
};

frappe.pages["whatsapp-setup"].on_page_show = function (wrapper) {
	if (wrapper.whatsapp_setup) wrapper.whatsapp_setup.refresh();
};

/** The WhatsApp Setup page: connected numbers, the two ways to connect, and the results. */
class WhatsAppSetupPage {
	/**
	 * Build the page.
	 *
	 * @param {object} page - The Frappe app page.
	 */
	constructor(page) {
		this.page = page;
		this.$body = $(`<div class="wac-setup"></div>`).appendTo(page.main);
		this.refresh();
	}

	/**
	 * Load the accounts and the hub setting, then draw the page.
	 *
	 * @returns {void}
	 */
	refresh() {
		frappe.call({ method: `${SETUP_API}.get_status`, type: "GET" }).then((r) => {
			this.status = r.message.data;
			this.render();
		});
	}

	/**
	 * Draw the page from this.status.
	 *
	 * @returns {void}
	 */
	render() {
		const esc = frappe.utils.escape_html;
		const { accounts, hub_url } = this.status;
		const rows = accounts
			.map(
				(a) => `
			<div class="wac-setup-row">
				<span class="indicator-pill ${a.enabled ? "green" : "gray"}">${
					a.enabled ? __("Enabled") : __("Disabled")
				}</span>
				<a class="wac-setup-name" href="/app/whatsapp-account/${encodeURIComponent(a.name)}">${esc(
					a.name
				)}</a>
				<span class="wac-setup-number">${esc(a.display_phone_number || "")}</span>
				<span class="text-muted">${esc(__(a.setup_method || "Manual"))}</span>
				<span class="wac-setup-actions">
					<button class="btn btn-xs btn-default" data-test="${esc(a.name)}">${__("Test")}</button>
					<button class="btn btn-xs btn-default" data-steps="${esc(a.name)}">${__(
					"Run Setup Again"
				)}</button>
				</span>
			</div>`
			)
			.join("");
		this.$body.html(`
			<p class="wac-setup-lead">${__(
				"Connect a WhatsApp Business number to this site. The setup checks the number, connects webhooks, syncs templates and tests everything."
			)}</p>
			${accounts.length ? `<h4>${__("Your numbers")}</h4><div class="wac-setup-list">${rows}</div>` : ""}
			<h4>${__("Connect a number")}</h4>
			<div class="wac-setup-choices">
				<div class="wac-setup-choice">
					<h5>${__("Connect with Facebook")} <span class="indicator-pill blue">${__(
			"Recommended"
		)}</span></h5>
					<p>${__(
						"Log in with Facebook, choose or create your business, add your number and verify it with a code. No Meta app, token or webhook to set up."
					)}</p>
					<label class="wac-setup-check"><input type="checkbox" class="wac-coexistence">
						${__("This number already uses the WhatsApp Business app on a phone")}</label>
					<button class="btn btn-primary wac-facebook" ${hub_url ? "" : "disabled"}>${__(
			"Connect with Facebook"
		)}</button>
					${
						hub_url
							? ""
							: `<p class="text-muted small">${__(
									"Set the Hub URL in WhatsApp Settings to use this."
							  )}</p>`
					}
				</div>
				<div class="wac-setup-choice">
					<h5>${__("Use my own Meta app")}</h5>
					<p>${__(
						"For businesses that already have a Meta app with WhatsApp and a system user token. The webhook is set for you."
					)}</p>
					<button class="btn btn-default wac-own-app">${__("Enter App Details")}</button>
				</div>
			</div>
			<div class="wac-setup-results">${
				this.last_result ? whatsapp_connect.setup.steps_html(this.last_result) : ""
			}</div>`);
		this.$body.find(".wac-facebook").on("click", () => this.connect_with_facebook());
		this.$body
			.find(".wac-own-app")
			.on("click", () =>
				whatsapp_connect.setup.own_app_dialog((result) => this.show_result(result))
			);
		this.$body.find("[data-test]").on("click", (e) => {
			const name = $(e.currentTarget).attr("data-test");
			whatsapp_connect.setup.test_dialog(accounts.find((a) => a.name === name));
		});
		this.$body.find("[data-steps]").on("click", (e) => {
			frappe
				.call({
					method: `${SETUP_API}.run_steps`,
					args: { account: $(e.currentTarget).attr("data-steps") },
					freeze: true,
					freeze_message: __("Running the setup steps..."),
				})
				.then((r) => this.show_result(r.message.data));
		});
	}

	/**
	 * Run Embedded Signup in a popup from the hub, then claim the result.
	 *
	 * @returns {void}
	 */
	connect_with_facebook() {
		// Open the popup during the click, or the browser blocks it.
		const popup = window.open("", "whatsapp_signup", "width=720,height=820");
		const coexistence = this.$body.find(".wac-coexistence").is(":checked") ? 1 : 0;
		frappe
			.call({ method: `${SETUP_API}.start_hub_signup`, args: { coexistence } })
			.then((r) => {
				const { session, signup_url } = r.message.data;
				if (popup) popup.location.href = signup_url;
				else window.open(signup_url, "whatsapp_signup");
				this.wait_for_signup(session, new URL(signup_url).origin);
			})
			.catch(() => popup && popup.close());
	}

	/**
	 * Wait for the hub page's message, or for the user to say the signup is done.
	 *
	 * @param {string} session - The signup session.
	 * @param {string} hub_origin - Origin of the hub page.
	 * @returns {void}
	 */
	wait_for_signup(session, hub_origin) {
		const complete = () => {
			window.removeEventListener("message", on_message);
			dialog.hide();
			frappe
				.call({
					method: `${SETUP_API}.complete_hub_signup`,
					args: { session },
					freeze: true,
					freeze_message: __("Setting up your number..."),
				})
				.then((r) => this.show_result(r.message.data));
		};
		const on_message = (event) => {
			const data = event.data || {};
			if (event.origin === hub_origin && data.type === "whatsapp_connect_signup") {
				if (data.session === session && data.status === "connected") complete();
			}
		};
		window.addEventListener("message", on_message);
		const dialog = new frappe.ui.Dialog({
			title: __("Finish in the Facebook window"),
			fields: [
				{
					fieldtype: "HTML",
					options: `<p>${__(
						"Log in, choose your business and number, and verify the number. This page continues by itself when you finish."
					)}</p>`,
				},
			],
			primary_action_label: __("I Have Finished"),
			primary_action: complete,
		});
		dialog.onhide = () => window.removeEventListener("message", on_message);
		dialog.show();
	}

	/**
	 * Show the result of the setup steps and reload the accounts.
	 *
	 * @param {object} result - {account, steps}.
	 * @returns {void}
	 */
	show_result(result) {
		this.last_result = result;
		this.refresh();
	}
}
