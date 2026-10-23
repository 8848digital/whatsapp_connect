# Background Jobs

Frappe uses Python RQ (Redis Queue) for background job processing.

## Enqueue a job

````python
import frappe

frappe.enqueue(
    "<app_name>.<module_name>.tasks.send_report",  # dotted path to function
    queue="default",                                 # short, default, long
    timeout=300,                                     # seconds
    report_name="Monthly Summary"                    # kwargs passed to function
)
````

The function lives in `<module_name>/tasks.py` (see `CLAUDE.md`'s tree) and
must be importable:
````python
# apps/<app_name>/<app_name>/<module_name>/tasks.py
import frappe

def send_report(report_name: str) -> None:
    """
    Generate and send the named report to its configured recipients.

    Parameters:
        report_name (str, required): The report to generate and send.

    Returns:
        None
    """
    # ... generate and send report
````

## Queue types

| Queue | Use for | Default timeout |
|-------|---------|----------------|
| `short` | Quick tasks < 5 min | 300s |
| `default` | Normal tasks | 300s |
| `long` | Heavy tasks (exports, bulk ops) | 1500s |

## Enqueue options

````python
frappe.enqueue(
    method="<app_name>.<module_name>.tasks.process",
    queue="long",
    timeout=1500,
    is_async=True,           # False to run synchronously (for debugging)
    now=False,               # True to run inline immediately
    at_front=False,          # True to push to front of queue
    job_id="unique_id",      # prevent duplicate jobs
    deduplicate=True,        # skip if same job_id is already queued
    enqueue_after_commit=True,  # only enqueue after DB commit
)
````

## Scheduled jobs

Define in `hooks.py`:
````python
# hooks.py
scheduler_events = {
    "daily": [
        "<app_name>.<module_name>.tasks.daily_cleanup"
    ],
    "hourly": [
        "<app_name>.<module_name>.tasks.sync_data"
    ],
    "cron": {
        "0 9 * * 1": [           # every Monday at 9 AM
            "<app_name>.<module_name>.tasks.weekly_report"
        ]
    }
}
````

Scheduler intervals: `all` (every 5 min), `hourly`, `daily`, `weekly`, `monthly`, `cron`.

If `<module_name>/tasks.py` grows past ~300 lines (see `code-style`
SKILL.md), split by feature — `tasks_billing.py`, `tasks_notifications.py` —
rather than one catch-all file, same principle as `utils.py`'s anti-pattern
rule.

## Checking job status

````python
from frappe.utils.background_jobs import get_jobs

jobs = get_jobs(site=frappe.local.site, queue="default")
````

## Common pitfalls

- Background jobs run in a separate worker process — they do NOT share state with the web request. Always pass data via arguments.
- Always specify `site` if the function needs `frappe.db` or other site context.
- Use `enqueue_after_commit=True` when the job depends on data written in the current request.

## Document-context jobs

````python
frappe.enqueue_doc(
    "Expense",                      # doctype
    "EXP-0001",                     # name
    "send_notification",            # method name on the Document class
    queue="short",
    timeout=300,
    now=False,
)
````

`enqueue_doc` loads the document and calls `doc.send_notification()` in the
worker. Preferred when the job logic is a method on the Document controller.
`send_notification` here is a plain controller method (not whitelisted) —
see `controllers.md` for the whitelisting rules if this also needs a
client-facing entry point.