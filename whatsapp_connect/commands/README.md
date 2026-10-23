<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# Custom Export Fixtures Command

## Overview

- **`8848-export-fixtures`**: Custom bench command for exporting fixtures with enhanced data cleaning.

### What it does
- Reads fixture definitions from the app's own `custom_fixtures` hook (not Frappe's built-in `fixtures` hook).
- Exports data to `[app]/fixtures/`.
- Removes fields with null, empty string, or zero values.
- Keeps fixture JSON small and diff-friendly.

## Setup

**Step 1:** Copy this folder's files verbatim into your app:

```bash
apps/<app_name>/<app_name>/commands/
├── __init__.py
├── export_fixtures.py
└── README.md
```

**Step 2:** Wire `custom_fixtures` and `commands` in `apps/<app_name>/<app_name>/hooks.py`:

```python
custom_fixtures = [
    # Export Custom Field for a specific module
    {"dt": "Custom Field", "filters": {"module": "<Module Name>"}},
]

commands = ["<app_name>.commands.export_fixtures.export_fixtures"]
```

## Example Usage

### Export all custom fixtures
```bash
bench --site <site> 8848-export-fixtures
```

### Export custom fixtures for a specific app
```bash
bench --site <site> 8848-export-fixtures --app <app_name>
```

## `8848-export-fixtures` vs. built-in `export-fixtures`

| Feature | `export-fixtures` (built-in) | `8848-export-fixtures` (this command) |
| ---------------------- | ----------------- | ---------------------- |
| **Hook source** | `fixtures` | `custom_fixtures` |
| **Data cleaning** | None | Automatic cleanup of empty/null values |
| **Fixture size** | Larger (includes all data) | Smaller (optimized data) |

## Notes

- This command is additive — it doesn't replace Frappe's built-in `export-fixtures`, it exists alongside it for fixtures declared via `custom_fixtures`.
