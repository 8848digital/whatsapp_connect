#!/usr/bin/env bash
# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt
#
# Update one Frappe app repo that already has the 8848 setup (see
# project_base_template/custom_app_setup.md §4.10) from the latest skills
# repo. This only updates; it does not set up a new app.
#
# The script runs from two places:
#   - Inside the app, as scripts/sync_skills.sh: it clones the latest skills
#     repo to a temp folder, runs the script from that clone on this app,
#     then deletes the clone. APP_PATH defaults to this app.
#   - Inside a clone of the skills repo: it pulls the clone, then updates
#     the app at APP_PATH (default: the current directory).
#
# Updated in the app:
#   .claude/skills/                  from .claude/skills/
#   CLAUDE.md                        from CLAUDE.md
#   <app>/commands/                  from project_base_template/commands/
#   <app>/utils/api_handlers/        from project_base_template/api_handlers/
#                                    (<app_name> replaced with the app name)
#   scripts/sync_skills.sh           this script, so the app can run it later
#
# Usage:
#   scripts/sync_skills.sh [options] [APP_PATH]
#
# Options:
#   --no-pull      Do not run "git pull" on the skills repo clone first.
#   --force        Update even if the app has uncommitted changes in the
#                  updated paths (those changes are overwritten).
#   --dry-run      Show what would change, but change nothing.
#   -h, --help     Show this help.
#
# Environment (only used when the script runs from inside the app):
#   SKILLS_REPO_URL  Skills repo to clone
#                    (default: https://github.com/8848digital/skills.git).
#   SKILLS_BRANCH    Branch to clone (default: 8848-skills).
#
# Project-local skills in the app's .claude/skills/ are kept. A skill removed
# from this repo is removed from the app on the next run (tracked in
# MANIFEST_NAME). Other files in commands/ and utils/api_handlers/ are kept.
# A commands/ or utils/api_handlers/ folder the app does not have is skipped.
# The script does not commit; review with "git status" in the app.

set -euo pipefail

DEFAULT_REPO_URL="https://github.com/8848digital/skills.git"
SKILLS_REPO_URL="${SKILLS_REPO_URL:-$DEFAULT_REPO_URL}"
SKILLS_BRANCH="${SKILLS_BRANCH:-8848-skills}"

# Resolve symlinks, so a link to the script still finds the repo the real
# script lives in. That repo is either a skills repo clone or an app repo.
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SKILLS_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
SOURCE_SKILLS="$SKILLS_ROOT/.claude/skills"
TEMPLATE_DIR="$SKILLS_ROOT/project_base_template"
MANIFEST_NAME=".synced-from-8848-skills"
COMMAND_FILES=(__init__.py export_fixtures.py README.md)
API_HANDLER_FILES=(envelope.py error_messages.py response_formatter.py)

DO_PULL=1
FORCE=0
DRY_RUN=0
TARGET=""
APP_NAME=""
CLONE_DIR=""
ORIGINAL_ARGS=("$@")

usage() {
	# Print the header comment block (from line 7 to the first non-comment
	# line) as help text.
	awk 'NR < 7 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$SCRIPT_PATH"
}

die() {
	# Print an error and exit.
	echo "error: $*" >&2
	exit 1
}

parse_args() {
	# Fill DO_PULL, FORCE, DRY_RUN and TARGET from the command line.
	while [[ $# -gt 0 ]]; do
		case "$1" in
			--no-pull) DO_PULL=0; shift ;;
			--force) FORCE=1; shift ;;
			--dry-run) DRY_RUN=1; shift ;;
			-h|--help) usage; exit 0 ;;
			-*) die "unknown option: $1" ;;
			*)
				[[ -z "$TARGET" ]] || die "give one app path only"
				TARGET="$1"; shift
				;;
		esac
	done
	# Inside an app, the app is the repo this script lives in.
	if [[ -z "$TARGET" ]]; then
		if in_skills_repo; then TARGET="$PWD"; else TARGET="$SKILLS_ROOT"; fi
	fi
}

in_skills_repo() {
	# Return 0 if this script runs from a skills repo clone (not from an app).
	[[ -d "$SOURCE_SKILLS" && -d "$TEMPLATE_DIR" ]]
}

check_app_repo() {
	# Exit unless TARGET is the root of a Frappe app git repo that already
	# has the 8848 setup. Sets APP_NAME to the app's Python package name.
	[[ -d "$TARGET" ]] || die "not a directory: $TARGET"
	TARGET="$(cd "$TARGET" && pwd)"
	if in_skills_repo && [[ "$TARGET" == "$SKILLS_ROOT" ]]; then
		die "$TARGET is the skills repo itself"
	fi
	if [[ -d "$TARGET/apps" && -d "$TARGET/sites" ]]; then
		die "$TARGET is a bench; run this inside one app (apps/<app>) instead"
	fi

	local top hooks
	top="$(git -C "$TARGET" rev-parse --show-toplevel 2>/dev/null)" \
		|| die "$TARGET is not a git repo"
	[[ "$top" == "$TARGET" ]] || die "$TARGET is not the app repo root (root is $top)"

	hooks=("$TARGET"/*/hooks.py)
	[[ -f "${hooks[0]}" ]] || die "$TARGET is not a Frappe app (no <app>/hooks.py)"
	[[ ${#hooks[@]} -eq 1 ]] || die "more than one <app>/hooks.py in $TARGET"
	APP_NAME="$(basename "$(dirname "${hooks[0]}")")"

	if [[ ! -d "$TARGET/.claude/skills" && ! -f "$TARGET/CLAUDE.md" ]]; then
		die "$TARGET has no .claude/skills or CLAUDE.md; this script only updates." \
			"Set up the app first: project_base_template/custom_app_setup.md §4.10"
	fi
}

check_clean() {
	# Exit if the app has uncommitted changes in the paths this script updates.
	[[ $FORCE -eq 0 ]] || return 0
	local changes
	changes="$(git -C "$TARGET" status --porcelain -- \
		.claude/skills CLAUDE.md "$APP_NAME/commands" "$APP_NAME/utils/api_handlers" \
		scripts/sync_skills.sh)"
	[[ -z "$changes" ]] && return 0
	echo "$changes" >&2
	die "uncommitted changes in the paths above (commit them, or use --force)"
}

run_from_fresh_clone() {
	# Clone the latest skills repo to a temp folder, run its copy of this
	# script on TARGET, then delete the clone (EXIT trap). Used when the
	# script runs from inside an app, which has no skills repo next to it.
	local clone_opts=(--quiet --depth 1 --branch "$SKILLS_BRANCH") pass_args=(--no-pull)
	[[ $FORCE -eq 1 ]] && pass_args+=(--force)
	[[ $DRY_RUN -eq 1 ]] && pass_args+=(--dry-run)

	CLONE_DIR="$(mktemp -d)"
	trap 'rm -rf "$CLONE_DIR"' EXIT
	echo "==> Cloning latest skills from $SKILLS_REPO_URL ($SKILLS_BRANCH)"
	git clone "${clone_opts[@]}" "$SKILLS_REPO_URL" "$CLONE_DIR/skills" \
		|| die "could not clone branch $SKILLS_BRANCH of $SKILLS_REPO_URL (check your git access)"
	[[ -f "$CLONE_DIR/skills/scripts/sync_skills.sh" ]] \
		|| die "the cloned skills repo has no scripts/sync_skills.sh"

	bash "$CLONE_DIR/skills/scripts/sync_skills.sh" "${pass_args[@]}" "$TARGET"
}

pull_skills_repo() {
	# Fast-forward the skills repo. If the pull changed this script, run the
	# new version instead, so fixes to the script apply on the same run.
	local before after
	echo "==> Pulling latest skills in $SKILLS_ROOT"
	before="$(git -C "$SKILLS_ROOT" hash-object "$SCRIPT_PATH")"
	git -C "$SKILLS_ROOT" pull --ff-only \
		|| die "could not fast-forward the skills repo; fix it, or use --no-pull"
	after="$(git -C "$SKILLS_ROOT" hash-object "$SCRIPT_PATH")"
	if [[ "$before" != "$after" ]]; then
		echo "==> Script was updated; running the new version"
		exec "$SCRIPT_PATH" --no-pull "${ORIGINAL_ARGS[@]}"
	fi
}

sync_skills() {
	# Mirror each upstream skill into the app, drop skills removed upstream,
	# then write the manifest of synced skill names.
	local dest="$TARGET/.claude/skills" skill name
	# Compare by content (-c), not by time: a fresh clone gives every file a
	# new mtime, and -a would then copy and list every file on each run.
	local rsync_opts=(-rlpc --delete --out-format="%n")
	[[ $DRY_RUN -eq 1 ]] && rsync_opts+=(--dry-run)
	echo "--- .claude/skills/"

	remove_dropped_skills "$dest"
	mkdir -p "$dest"
	for skill in "$SOURCE_SKILLS"/*/; do
		name="$(basename "$skill")"
		rsync "${rsync_opts[@]}" "$skill" "$dest/$name/" | grep -v '/$' | sed "s|^|    $name/|" || true
	done

	[[ $DRY_RUN -eq 1 ]] || (cd "$SOURCE_SKILLS" && ls -1d */ | tr -d '/') > "$dest/$MANIFEST_NAME"
}

remove_dropped_skills() {
	# Delete skills listed in the old manifest that no longer exist upstream.
	local dest="$1" name
	[[ -f "$dest/$MANIFEST_NAME" ]] || return 0
	while IFS= read -r name; do
		[[ -n "$name" && ! -d "$SOURCE_SKILLS/$name" && -d "$dest/$name" ]] || continue
		echo "    remove  $name/ (dropped upstream)"
		[[ $DRY_RUN -eq 1 ]] || rm -rf "${dest:?}/$name"
	done < "$dest/$MANIFEST_NAME"
}

sync_claude_md() {
	# Replace the app's CLAUDE.md with the upstream one.
	echo "--- CLAUDE.md"
	update_file "$SKILLS_ROOT/CLAUDE.md" "$TARGET/CLAUDE.md"
}

sync_commands() {
	# Update the template files in <app>/commands/, verbatim.
	local dest="$TARGET/$APP_NAME/commands" file
	echo "--- $APP_NAME/commands/"
	[[ -d "$dest" ]] || { echo "    skip: folder not in the app (set up per custom_app_setup.md §4.7)"; return 0; }
	for file in "${COMMAND_FILES[@]}"; do
		update_file "$TEMPLATE_DIR/commands/$file" "$dest/$file"
	done
}

sync_api_handlers() {
	# Update the template files in <app>/utils/api_handlers/, with the
	# <app_name> token replaced by the real app name (custom_app_setup.md §4.9).
	local dest="$TARGET/$APP_NAME/utils/api_handlers" file rendered
	echo "--- $APP_NAME/utils/api_handlers/"
	[[ -d "$dest" ]] || { echo "    skip: folder not in the app (set up per custom_app_setup.md §4.9)"; return 0; }

	rendered="$(mktemp)"
	for file in "${API_HANDLER_FILES[@]}"; do
		sed "s/<app_name>/$APP_NAME/g" "$TEMPLATE_DIR/api_handlers/$file" > "$rendered"
		update_file "$rendered" "$dest/$file"
	done
	rm -f "$rendered"

	[[ -f "$dest/__init__.py" || $DRY_RUN -eq 1 ]] || touch "$dest/__init__.py"
}

sync_self() {
	# Copy this script into the app's scripts/ folder, so the app can run
	# the next update without a skills repo clone.
	local dest="$TARGET/scripts/sync_skills.sh"
	echo "--- scripts/sync_skills.sh"
	[[ $DRY_RUN -eq 1 ]] || mkdir -p "$TARGET/scripts"
	update_file "$SCRIPT_PATH" "$dest"
	[[ $DRY_RUN -eq 1 ]] || chmod +x "$dest"
}

update_file() {
	# Copy SOURCE over DEST if their content differs; report what changed.
	local source="$1" dest="$2"
	cmp -s "$source" "$dest" && return 0
	if [[ -f "$dest" ]]; then
		echo "    update  ${dest#"$TARGET"/}"
	else
		echo "    add     ${dest#"$TARGET"/}"
	fi
	[[ $DRY_RUN -eq 1 ]] || cp "$source" "$dest"
}

main() {
	# Check the app, get the latest skills repo, then update the synced parts.
	parse_args "$@"
	check_app_repo
	check_clean
	if ! in_skills_repo; then
		run_from_fresh_clone
		return 0
	fi
	[[ $DO_PULL -eq 1 ]] && pull_skills_repo

	echo "==> Updating $TARGET (app: $APP_NAME)"
	sync_skills
	sync_claude_md
	sync_commands
	sync_api_handlers
	sync_self

	echo
	echo "Synced at skills commit $(git -C "$SKILLS_ROOT" rev-parse --short HEAD)."
	[[ $DRY_RUN -eq 1 ]] && echo "Dry run: nothing was changed."
	return 0
}

main "$@"
