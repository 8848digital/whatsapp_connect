# Whitelisted APIs

## Location rule (read this first)

All whitelisted, REST-style endpoint code lives in **exactly one place**:

````
apps/<app_name>/<app_name>/<module_name>/api/
````

- `<module_name>` must not be the same name as `<app_name>`.
- No `api.py` file or `api/` folder may exist inside `doctype/`,
  `customization/`, the app root, or anywhere else. If an endpoint is scoped
  to a specific doctype or customization, it still lives under
  `<module_name>/api/` (versioned), not alongside that doctype/customization.
- **`@frappe.whitelist()` must never be used inside a `doctype/<name>/<name>.py`
  controller file or a `customization/<name>/*.py` file** — not as a
  `Document` class method, and not as a module-level function. A controller
  method (e.g. `approve()`) is plain, non-whitelisted Python. If it needs to
  be reachable from the client, write a whitelisted function under
  `<module_name>/api/` that loads the document and calls the controller
  method internally.
- **Non-whitelisted support helpers used by the API layer** — centralised
  error handling, pre-request guards, response formatting — are *not*
  endpoint code, so they don't live in `api/` either. They live in
  `apps/<app_name>/<app_name>/utils/api_handlers/` at the app root, shared
  by every module's `api/vN/` files. See the Helper section below.
- Dotted import/method paths throughout this file use the placeholder
  `<app_name>.<module_name>` — substitute your actual app and module names.

## Mandatory docstring for every whitelisted function

Every `@frappe.whitelist()` function — all of which live under
`<module_name>/api/` — must have a docstring with:

- A 2–3 line explanation of what the function does.
- The endpoint path and HTTP method.
- Every parameter, with its type and whether it's required/optional.
- The response format.

````python
# apps/<app_name>/<app_name>/<module_name>/api/v1/bank.py

@frappe.whitelist(methods=["POST"])
def update_player_bank_account(
    player_id: str,
    account_name: str,
    bank_name: str,
    bank_account_no: str,
    bank_code: str,
    first_name: str,
    last_name: str,
):
    """
    Update a player's bank account details used for withdrawal processing.
    Validates the account fields and persists them against the player's
    linked bank account record.

    **Endpoint:** `/api/method/<app_name>.<module_name>.api.v1.bank.update_player_bank_account`
    **HTTP Method:** POST
    **Parameters:**
        - player_id (str, required): The player ID
        - account_name (str, required): The account name
        - bank_name (str, required): The bank name
        - bank_account_no (str, required): The bank account number
        - bank_code (str, required): The bank code
        - first_name (str, required): The first name
        - last_name (str, required): The last name
    **Response:**
```json
        {
            "status": true,
            "status_code": 200,
            "message": "Bank account updated successfully",
            "data": { "player_id": "PLYR-0001" },
            "errors": null
        }
```
    """
    ...
````

## Controller methods are never whitelisted

DocType controllers (`doctype/<name>/<name>.py`) and customization files
(`customization/<name>/*.py`) hold plain business logic and lifecycle hooks
only — `before_save`, `on_submit`, `validate`, ordinary helper methods, etc.
None of these are decorated with `@frappe.whitelist()`.

````python
# apps/<app_name>/<app_name>/<module_name>/doctype/expense/expense.py

import frappe
from frappe.model.document import Document

class Expense(Document):
    def approve(self):
        """
        Mark this expense as approved. Plain controller method — not
        whitelisted, not directly callable from the client.

        Parameters:
            None (operates on self).

        Returns:
            str: The updated status ("Approved").
        """
        self.status = "Approved"
        self.save()
        return self.status
````

The business logic that fetches the document and invokes the controller
method also stays out of `api/` — it belongs in a business-logic module
(e.g. alongside the controller, or in `customization/`'s `utils.py`
equivalent):

````python
# apps/<app_name>/<app_name>/<module_name>/doctype/expense/expense_utils.py

import frappe

def approve_expense(expense_id: str) -> str:
    """
    Load an Expense document and approve it. Plain business-logic function —
    not whitelisted; called by the api/ wrapper below.

    Parameters:
        expense_id (str, required): The name of the Expense document.

    Returns:
        str: The document's status after approval.
    """
    doc = frappe.get_doc("Expense", expense_id)
    doc.approve()
    return doc.status
````

The whitelisted function under `<module_name>/api/` is a **thin wrapper
only** — it validates input, calls the business-logic function, and formats
the response. It must never contain business logic itself (no
`frappe.get_doc`, no mutating fields, no calling `doc.save()` directly):

````python
# apps/<app_name>/<app_name>/<module_name>/api/v1/expense.py

import frappe
from <app_name>.<module_name>.doctype.expense.expense_utils import approve_expense
from <app_name>.utils.api_handlers.response_formatter import api_response

@frappe.whitelist(methods=["POST"])
def approve_expense_endpoint(expense_id: str):
    """
    Approve an expense and mark it ready for reimbursement.

    **Endpoint:** `/api/method/<app_name>.<module_name>.api.v1.expense.approve_expense_endpoint`
    **HTTP Method:** POST
    **Parameters:**
        - expense_id (str, required): The name of the Expense document
    **Response:**
```json
        {
            "status": true,
            "status_code": 200,
            "message": "Expense approved",
            "data": { "status": "Approved" },
            "errors": null
        }
```
    """
    status = approve_expense(expense_id)
    return api_response(message="Expense approved", data={"status": status})
````

Call from client JS:
````javascript
frappe.call({
    method: "<app_name>.<module_name>.api.v1.expense.approve_expense_endpoint",
    args: { expense_id: frm.doc.name },
    callback(r) { console.log(r.message); }
});
````

This keeps every whitelisted entry point auditable from a single folder —
you never have to check `doctype/` or `customization/` files to find out
what's reachable from the client — and keeps `api/` free of business logic,
which stays testable independent of the HTTP layer.

## Standalone API files (all whitelisted logic, DocType-related or not)

Every whitelisted function — whether it wraps a single document, aggregates
across documents, or has no document context at all — lives under
`<module_name>/api/`.

````python
# apps/<app_name>/<app_name>/<module_name>/dashboard.py — plain business logic, not whitelisted
import frappe

def get_dashboard_counts() -> dict:
    """
    Compute aggregate counts used by the dashboard. Plain business-logic
    function — not whitelisted, and lives outside `api/` entirely.

    Parameters:
        None.

    Returns:
        dict: {"total": <int>}
    """
    return {"total": frappe.db.count("Expense")}
````

````python
# apps/<app_name>/<app_name>/<module_name>/api/v1/dashboard.py
import frappe
from <app_name>.<module_name>.dashboard import get_dashboard_counts

@frappe.whitelist(methods=["GET"])
def get_dashboard_data():
    """
    Return aggregate counts used by the main dashboard widget.

    **Endpoint:** `/api/method/<app_name>.<module_name>.api.v1.dashboard.get_dashboard_data`
    **HTTP Method:** GET
    **Parameters:** None
    **Response:**
```json
        {
            "status": true,
            "status_code": 200,
            "message": "Dashboard data fetched successfully",
            "data": { "total": 42 },
            "errors": null
        }
```
    """
    return get_dashboard_counts()
````

For larger apps, organize by feature:
````
apps/<app_name>/<app_name>/<module_name>/api/
    __init__.py
    v1/
        expenses.py
        reports.py
apps/<app_name>/<app_name>/utils/
    api_handlers/
        response_formatter.py
        envelope.py
        error_messages.py

````

There is no doctype-scoped or customization-scoped `api.py` variant, and no
whitelisted method lives on a controller class. If an endpoint is logically
tied to one doctype (e.g. bank details on Customer), it still belongs in
`<module_name>/api/v1/<feature>.py` (e.g. `bank.py`), and simply imports
whatever controller/business-logic module it needs and calls its
(non-whitelisted) methods.

## Allow guest access

````python
# apps/<app_name>/<app_name>/<module_name>/api/v1/misc.py

@frappe.whitelist(allow_guest=True)
def public_endpoint():
    """
    Return a static greeting. Guest-accessible health-check style endpoint.

    **Endpoint:** `/api/method/<app_name>.<module_name>.api.v1.misc.public_endpoint`
    **HTTP Method:** GET
    **Parameters:** None
    **Response:**
```json
        {
            "status": true,
            "status_code": 200,
            "message": "Success",
            "data": { "message": "Hello" },
            "errors": null
        }
```
    """
    return {"message": "Hello"}
````

Without `allow_guest=True`, the endpoint requires authentication.

## Argument handling

- **Always add type hints** to whitelisted method parameters. Frappe validates and casts arguments based on type hints, preventing type-confusion attacks:
````python
# apps/<app_name>/<app_name>/<module_name>/doctype/expense/expense_utils.py

import frappe

def create_new_expense(title: str, amount: float, tags: list | None = None) -> str:
    """
    Create and insert a new Expense document. Plain business-logic
    function — not whitelisted.

    Parameters:
        title (str, required): Expense title.
        amount (float, required): Expense amount.
        tags (list, optional): Optional list of tags.

    Returns:
        str: The name of the newly-created Expense document.
    """
    doc = frappe.get_doc({
        "doctype": "Expense",
        "title": title,
        "amount": amount,
        "tags": tags or [],
    })
    doc.insert()
    return doc.name
````

````python
# apps/<app_name>/<app_name>/<module_name>/api/v1/expenses.py

import frappe
from <app_name>.<module_name>.doctype.expense.expense_utils import create_new_expense

@frappe.whitelist(methods=["POST"])
def create_expense(title: str, amount: float, tags: list | None = None):
    """
    Create a new expense record.

    **Endpoint:** `/api/method/<app_name>.<module_name>.api.v1.expenses.create_expense`
    **HTTP Method:** POST
    **Parameters:**
        - title (str, required): Expense title
        - amount (float, required): Expense amount
        - tags (list, optional): Optional list of tags
    **Response:**
```json
        {
            "status": true,
            "status_code": 201,
            "message": "Expense created successfully",
            "data": { "name": "EXP-0002" },
            "errors": null
        }
```
    """
    # title is guaranteed to be str, amount is cast to float
    # Without type hints, all args arrive as untrusted strings
    name = create_new_expense(title, amount, tags)
    return {"name": name}
````

- Use `frappe.form_dict` for raw request data:
````python
data = frappe.form_dict
````

## Return values

- Return a dict/list → auto-serialized to JSON under `{"message": <return_value>}`
- For custom HTTP responses:
````python
frappe.response["meta"] = meta
````

## API response standard

Every custom-built API (under `<module_name>/api/`) must return a consistent response shape rather than a raw dict, so frontend/client code can rely on one contract.

### Standard shape

````json
{
    "status": true,
    "status_code": 200,
    "message": "Success",
    "data": {},
    "errors": null
}
````

- `status` (bool, required) — success or failure
- `status_code` (int, required) — HTTP status code, must match the actual response status
- `message` (str, required) — human-readable, safe to show to a user
- `data` (object/array/null, required) — payload on success; `null` on failure
- `errors` (object/array/null, optional) — validation/business-rule error detail; `null` on success

### Examples

Success:
````json
{
    "status": true,
    "status_code": 200,
    "message": "Customer details fetched successfully",
    "data": { "customer": "CUST-0001", "customer_name": "ABC Pvt Ltd" },
    "errors": null
}
````

Validation error:
````json
{
    "status": false,
    "status_code": 400,
    "message": "Validation failed",
    "data": null,
    "errors": { "customer": "Customer is mandatory" }
}
````

### Status codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Record created |
| 204 | No content |
| 400 | Validation error |
| 401 | Authentication failed |
| 403 | Permission denied |
| 404 | Record not found |
| 409 | Duplicate record / conflict |
| 422 | Business rule validation failed |
| 429 | Too many requests |
| 500 | Internal server error |

### Rules

- Always return JSON with `status`, `status_code`, and `message` present.
- Never expose Python tracebacks or raw database errors — catch and translate into `message`/`errors`.
- `data` is populated only on success; leave it `null` on failure.
- `errors` carries validation/business-rule failure detail; leave it `null` on success.
- Keep `message` human-readable — it may be shown directly in a UI.
- The HTTP status actually returned must match `status_code` in the body.

### Helper — lives in `utils/api_handlers/`, not in `api/`

> **Do not hand-write these helpers.** `utils/api_handlers/` is populated by
> copying three canonical files **verbatim** from
> [`project_base_template/api_handlers/`](https://github.com/8848digital/skills/tree/8848-skills/project_base_template/api_handlers)
> in the skills repo:
>
> | File | What it holds |
> | ---- | ------------- |
> | `envelope.py` | The envelope builder + `api_response(...)` + `is_already_formatted(...)`. |
> | `error_messages.py` | Exception → HTTP-status mapping and message-sanitisation helpers. |
> | `response_formatter.py` | The `after_request` hook + success/error formatters; re-exports `api_response`. |
>
> After copying: replace the `<app_name>` token inside the files (the
> `Wired in hooks.py:` docstring line and the `/api/method/<app_name>` path
> check in `response_formatter.py`), then wire the hook in `hooks.py`. Full
> step-by-step: `project_base_template/custom_app_setup.md` §4.9. This
> section documents how the copied helpers behave — not code to retype.

There are **two** ways a response gets into the standard envelope, and both
ship in the copied files:

**1. The global `after_request` formatter (primary).** Wiring this in
`hooks.py` makes every `/api/method/<app_name>…` response — success *and*
error, whether the endpoint returned a raw dict or called `api_response`
itself — come out in the standard shape automatically:

````python
# hooks.py
after_request = ["<app_name>.utils.api_handlers.response_formatter.format_frappe_response_to_custom"]
````

Because of this hook, an endpoint may simply `return {...}` (raw payload)
and still produce a compliant envelope. The formatter is idempotent
(`is_already_formatted`), so wrapping twice is safe.

> **Frontend note:** once the `after_request` hook is wired, the HTTP body
> *is* the envelope (`{status, status_code, message, data, errors}`) — the
> payload is under `data`, and `message` is the human string. Desk clients
> should read `r.message.data` from `frappe.call` (or `res.data` from the
> raw response); **`frappe.xcall` will resolve to the envelope's `message`
> string, not the payload**, so use `frappe.call` and read `.data` for
> endpoints that go through this formatter.

**2. Calling `api_response(...)` explicitly (when you need a custom message
or status).** Import it — re-exported from `response_formatter.py` — into any
module's endpoint file, regardless of `<module_name>`:

````python
# apps/<app_name>/<app_name>/<module_name>/api/v1/expense.py
from <app_name>.utils.api_handlers.response_formatter import api_response

# api_response(status=True, code=200, message="", data=None, errors=None)
# -> {"status", "status_code", "message", "data", "errors"}
return api_response(message="Expense approved", data={"expense": name})
````

All three files live only in `utils/api_handlers/` at the app root — one
shared implementation, imported by every module's `api/vN/` files, never
duplicated per module and never placed inside `api/` itself.

## Frontend API structure (versioned APIs)

For apps serving a dedicated frontend (e.g. React), version the API surface separately from internal doctype APIs, so frontend contracts can evolve independently of internal logic. This still lives under `<module_name>/api/` — never at the app root.

````
apps/<app_name>/<app_name>/<module_name>/api/
    v1.py           # main v1 controller — routes/re-exports v1 endpoints
    v1/
        __init__.py
        cart.py
        item_list.py
        sales_order.py
````

- Version from the start (`v1/`, `v2/`, ...) even if only one version exists — retrofitting versioning later breaks existing frontend clients.
- Keep the top-level version file (e.g. `v1.py`) as the entry controller; it stays thin and routes to resource files under `v1/`.
- Split endpoints by resource/feature (`cart.py`, `sales_order.py`), not by HTTP verb or a single catch-all file.
- When introducing `v2`, keep `v1` intact and functioning — don't break existing frontend clients still pointed at v1. Only remove a version after all clients have migrated.
- Every endpoint under `api/vN/` follows the API response standard above, and every whitelisted function carries the mandatory docstring described earlier.

## Built-in document APIs (v2)

Frappe provides CRUD APIs automatically via `/api/v2/document/` — no need to write them. Requires **Frappe v15+**.

````
GET    /api/v2/document/<DocType>                          # list (with filters, fields, order_by, limit)
POST   /api/v2/document/<DocType>                          # create
GET    /api/v2/document/<DocType>/<name>/                  # read
PUT    /api/v2/document/<DocType>/<name>/                  # update
DELETE /api/v2/document/<DocType>/<name>/                  # delete
GET    /api/v2/document/<DocType>/<name>/copy              # copy doc
POST   /api/v2/method/<DocType>/<method>                   # call doctype level method (built-in Frappe methods only)
GET    /api/v2/doctype/<DocType>/meta                      # get DocType meta
GET    /api/v2/doctype/<DocType>/count                     # count records
````

Note: `POST /api/v2/document/<DocType>/<name>/method/<method>/` (calling a
custom whitelisted method directly on a document) does **not** apply in
this project's convention, since custom methods on controllers are never
whitelisted. Use a wrapper under `<module_name>/api/` instead, as shown
above.

### List query params
`fields` (JSON list), `filters` (JSON dict/list), `order_by`, `start`, `limit` (default 20), `group_by`.

Response includes `has_next_page` boolean for pagination.

### Bulk operations
````
POST /api/v2/document/<DocType>/bulk_delete   # body: {"names": [...]}
POST /api/v2/document/<DocType>/bulk_update   # body: {"docs": [{"name": "...", ...fields}]}
````

Large bulk operations (>20 items by default) are automatically enqueued as background jobs.

Only create custom `@frappe.whitelist()` endpoints (under `<module_name>/api/`) for logic that goes beyond CRUD.

## Specify HTTP methods

Always declare allowed HTTP methods explicitly. Frappe auto-commits only for POST/PUT — GET requests do not commit.

````python
@frappe.whitelist(methods=["GET"])
def get_dashboard_data(): ...

@frappe.whitelist(methods=["POST"])
def submit_entry(name: str): ...

@frappe.whitelist(methods=["GET", "POST"])
def get_or_create_token(): ...
````

(Each of the above still requires the full mandatory docstring — omitted here only for brevity, and each lives under `<module_name>/api/`.)

## Anti-patterns

- **Don't create `api.py` files or `api/` folders inside `doctype/`, `customization/`, or the app root.** All whitelisted endpoint code lives in exactly one place: `<module_name>/api/`.
- **Don't put `error_messages.py`/`envelope.py`/`response_formatter.py` inside `<module_name>/api/`.** They're non-whitelisted, cross-module helpers — their home is `apps/<app_name>/<app_name>/utils/api_handlers/` at the app root.
- **Don't name `<module_name>` the same as `<app_name>`.** They must be distinct.
- **Don't use `@frappe.whitelist()` inside `doctype/<name>/<name>.py` or `customization/<name>/*.py`.** Not as a class method, not as a module function. Controller files hold plain lifecycle logic only; write a wrapper under `<module_name>/api/` for anything the client needs to call.
- **Don't put doc-scoped logic in standalone APIs.** If the function fetches one doc and acts on it, keep the actual business logic in the controller's (non-whitelisted) method, and keep the `<module_name>/api/` wrapper thin — validate, delegate, format the response.
- **Don't write business logic inside `api/` files.** Files under `<module_name>/api/` should only contain thin whitelisted functions that validate input, call a business-logic function defined elsewhere, and format the response. A whitelisted function must never itself call `frappe.get_doc`, mutate a document, run a query, or otherwise implement the actual logic — that logic belongs in the controller (`doctype/`), customization module (`customization/`), or a plain utility module, and the `api/` function just calls it.
- **Don't return raw dicts or unstructured errors from custom endpoints.** Use the API response standard consistently so frontend code doesn't need per-endpoint special-casing.
- **Don't leak sensitive fields in guest APIs.** With `allow_guest=True`, only return fields guests need. Never expose `user` (email), internal IDs, or permission-sensitive data.
- **Don't skip the docstring.** Every whitelisted function must document its explanation, endpoint, HTTP method, parameters, and response format — this is not optional documentation, it's the contract reviewers and other agents rely on.