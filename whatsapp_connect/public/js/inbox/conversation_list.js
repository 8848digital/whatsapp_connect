// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

import { INBOX_API } from "./constants";

const STATUS_TABS = ["Open", "Pending", "Closed"];

/** The left panel: status tabs, filters, search and the conversations. */
export class ConversationList {
	/**
	 * Draw the filters; the rows come with refresh().
	 *
	 * @param {jQuery} $wrapper - The list panel.
	 * @param {Function} on_open - Called with the number of the clicked conversation.
	 */
	constructor($wrapper, on_open) {
		this.$wrapper = $wrapper;
		this.on_open = on_open;
		this.filters = { status: "Open", assigned_to: "", search: "" };
		this.active = null;
		this.render_frame();
	}

	/**
	 * Draw the tabs, the assignee filter and the search box.
	 *
	 * @returns {void}
	 */
	render_frame() {
		const tabs = [...STATUS_TABS, ""]
			.map(
				(status) => `
				<button class="wac-tab ${status === this.filters.status ? "active" : ""}" data-status="${status}">
					${status ? __(status) : __("All")} <span class="wac-tab-count"></span>
				</button>`
			)
			.join("");
		this.$wrapper.html(`
			<div class="wac-list-tabs">${tabs}</div>
			<div class="wac-list-filters">
				<input type="search" class="form-control input-xs wac-search" placeholder="${__(
					"Search name or number"
				)}">
				<select class="form-control input-xs wac-assignee">
					<option value="">${__("Everyone")}</option>
					<option value="me">${__("Assigned to me")}</option>
					<option value="unassigned">${__("Unassigned")}</option>
				</select>
			</div>
			<div class="wac-list-rows"></div>
		`);
		this.$wrapper.on("click", ".wac-tab", (event) => {
			this.filters.status = $(event.currentTarget).attr("data-status");
			this.$wrapper.find(".wac-tab").removeClass("active");
			$(event.currentTarget).addClass("active");
			this.refresh();
		});
		this.$wrapper.on("change", ".wac-assignee", (event) => {
			this.filters.assigned_to = $(event.currentTarget).val();
			this.refresh();
		});
		this.$wrapper.on(
			"input",
			".wac-search",
			frappe.utils.debounce((event) => {
				this.filters.search = $(event.target).val();
				this.refresh();
			}, 400)
		);
		this.$wrapper.on("click", ".wac-row", (event) => {
			this.on_open($(event.currentTarget).attr("data-number"));
		});
	}

	/**
	 * Load the conversations for the current filters and draw them.
	 *
	 * @returns {Promise} Resolves when the rows are drawn.
	 */
	refresh() {
		return frappe
			.call({ method: `${INBOX_API}.get_conversations`, type: "GET", args: this.filters })
			.then((r) => {
				const data = r.message.data;
				this.render_counts(data.counts);
				this.render_rows(data.conversations);
			});
	}

	/**
	 * Mark the open conversation in the list.
	 *
	 * @param {string} number - The customer's number.
	 * @returns {void}
	 */
	set_active(number) {
		this.active = number;
		this.$wrapper.find(".wac-row").removeClass("active");
		this.$wrapper.find(`.wac-row[data-number="${CSS.escape(number)}"]`).addClass("active");
	}

	/**
	 * Show the count of each status next to its tab.
	 *
	 * @param {object} counts - {"Open": 3, "Pending": 0, "Closed": 12}.
	 * @returns {void}
	 */
	render_counts(counts) {
		STATUS_TABS.forEach((status) => {
			this.$wrapper
				.find(`.wac-tab[data-status="${status}"] .wac-tab-count`)
				.text(counts[status] || "");
		});
	}

	/**
	 * Draw the conversation rows.
	 *
	 * @param {object[]} rows - Conversations from get_conversations.
	 * @returns {void}
	 */
	render_rows(rows) {
		const $rows = this.$wrapper.find(".wac-list-rows");
		if (!rows.length) {
			$rows.html(`<div class="wac-empty">${__("No conversations")}</div>`);
			return;
		}
		$rows.html(rows.map((row) => this.row_html(row)).join(""));
		if (this.active) this.set_active(this.active);
	}

	/**
	 * Build one conversation row.
	 *
	 * @param {object} row - A conversation.
	 * @returns {string} HTML of the row.
	 */
	row_html(row) {
		const esc = frappe.utils.escape_html;
		const unread = row.unread_count
			? `<span class="wac-unread">${row.unread_count}</span>`
			: `<span class="wac-unread wac-unread-empty"></span>`;
		const prefix = row.last_message_direction === "Outgoing" ? `${__("You")}: ` : "";
		const time = row.last_message_at
			? frappe.datetime.comment_when(row.last_message_at, true)
			: "";
		const assignee = row.assigned_to_name
			? `<span class="wac-row-assignee">${esc(row.assigned_to_name)}</span>`
			: "";
		return `
			<div class="wac-row ${row.unread_count ? "wac-row-unread" : ""}" data-number="${esc(
			row.phone_number
		)}">
				<div class="wac-avatar">${esc(frappe.get_abbr(row.display_name))}</div>
				<div class="wac-row-main">
					<div class="wac-row-top">
						<span class="wac-row-name ellipsis">${esc(row.display_name)}</span>
						<span class="wac-row-time">${time}</span>
					</div>
					<div class="wac-row-bottom">
						<span class="wac-row-preview ellipsis">${esc(prefix + (row.last_message_preview || ""))}</span>
						${assignee}
						${unread}
					</div>
				</div>
			</div>`;
	}
}
