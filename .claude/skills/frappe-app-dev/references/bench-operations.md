# Bench CLI Reference

Always use bare `bench`. Not `./env/bin/bench`.

## App & site lifecycle

````bash
# New app (MUST pipe input — no heredoc, no --no-input)
# Use "Proprietary" as <license> for 8848 Digital apps — see licensing.md;
# do not leave this as an OSS identifier (mit, apache-2.0, etc.)
printf '<title>\n<desc>\n<publisher>\n<email>\n<license>\nN\nN\nN\n' | bench new-app <app-name>

# New site (set root_password in common_site_config first: bench set-config -g root_password '<pwd>')
bench new-site <name>.localhost --admin-password admin

# Install/uninstall app
bench --site <site> install-app <app-name>
bench --site <site> uninstall-app <app-name>

# List apps on site
bench --site <site> list-apps

# Migrate (apply schema + data changes)
bench --site <site> migrate

# Set default site
bench use <site>
````

## Development

````bash
# Start dev server (run in BACKGROUND)
bench start

# Developer mode
bench set-config -g developer_mode 1

# Python console with site context
bench --site <site> console

# Execute a Python expression
bench --site <site> execute frappe.utils.get_url

# Execute with args and kwargs
bench --site <site> execute path.to.function arg1 arg2 --kwarg1 hello

# Run tests
bench --site <site> run-tests --app <app-name>
bench --site <site> run-tests --doctype "DocType Name"

# Build frontend assets
bench build --app <app-name>

# Watch mode for frontend
bench watch
````

## Site maintenance

````bash
# Backup
bench --site <site> backup

# Restore
bench --site <site> restore <path>

# Clear cache
bench --site <site> clear-cache
bench --site <site> clear-website-cache

# Set site config
bench --site <site> set-config <key> <value>

# Global config
bench set-config -g <key> <value>

# MariaDB console (debugging only)
bench --site <site> mariadb

# Drop site (DESTRUCTIVE)
bench drop-site <site> --db-root-password '<pwd>'
````

## Fixtures

````bash
# Export fixtures defined in hooks.py's `fixtures` hook
bench --site <site> export-fixtures --app <app-name>

# Custom command: export fixtures defined in hooks.py's `custom_fixtures` hook,
# stripping null/empty/zero-valued fields for smaller, diff-friendly JSON.
# Ships as a copy-pasteable template at project_base_template/commands/ —
# see that folder's README.md for setup, and CLAUDE.md's `commands/` entry
# for where it fits in the app structure.
bench --site <site> 8848-export-fixtures --app <app-name>
````

Template source: [`project_base_template/commands/`](https://github.com/8848digital/skills/tree/8848-skills/project_base_template/commands).
