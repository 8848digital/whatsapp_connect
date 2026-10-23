# Controllers

Controllers add server-side logic to DocTypes via Python classes.

## File location

````
apps/<app>/<app>/<module>/doctype/<doctype_name>/<doctype_name>.py
````

## Basic controller

````python
import frappe
from frappe.model.document import Document

class Expense(Document):
    def validate(self):
        if self.amount <= 0:
            frappe.throw("Amount must be positive")

    def before_save(self):
        self.total = sum(item.amount for item in self.items)
````

The class name is the DocType name with spaces removed (e.g. "Expense Category" → `ExpenseCategory`).

> For anything beyond a single simple expression, follow the file structure
> rules below — hooks should call out to a function, not contain the logic
> themselves.

## Document lifecycle hooks

Called in this order:

### On insert (new document)
1. `before_insert`
2. `before_naming` (before name is set)
3. `autoname` (custom naming logic — `self.name` is set after this)
4. `before_validate`
5. `validate`
6. `before_save`
7. (db insert)
8. `after_insert`
9. `on_update`
10. `after_save`
11. `on_change`

### On update (existing document)
1. `before_validate`
2. `validate`
3. `before_save`
4. (db update)
5. `on_update`
6. `after_save`
7. `on_change`

### On submit (submittable DocTypes)
1. `before_validate`
2. `validate`
3. `before_save`
4. `before_submit`
5. `on_submit`
6. `on_update`
7. `after_save`
8. `on_change`

### On cancel
1. `before_cancel`
2. `on_cancel`
3. `on_change`

### On delete
1. `on_trash`
2. `after_delete`

## File structure: hooks vs. logic

`<doctype_name>.py` (e.g. `operation_card.py`) is for wiring lifecycle hooks
(`validate`, `on_submit`, `on_cancel`, etc.) to logic — not for containing that
logic. Each hook should call out to a function rather than implement the
behavior inline.

````python
# operation_card.py — hooks only, delegate to helpers
import frappe
from frappe.model.document import Document
from <app_name>.<module_name>.doctype.operation_card.operation_card_utils import (
    validate_operation,
    apply_status,
)

class OperationCard(Document):
    def validate(self):
        validate_operation(self)

    def on_submit(self):
        apply_status(self, "Submitted")
````

- Place the actual implementation in sibling files within the same doctype
  directory (e.g. `operation_card_utils.py`, `operation_card_service.py`) —
  not inline in the hook method.
- **If a hook needs to update another doctype's records**, place that logic in
  *that* doctype's own directory (e.g. a function in
  `sales_order/sales_order_utils.py`) and call it from the triggering
  doctype's hook, rather than writing another doctype's update logic inline
  where the hook fires. This keeps each doctype's data-mutation logic owned
  by that doctype's module.
  - Exception: doctypes you don't own (core Frappe/ERPNext, or another app's
    doctype) — don't add files into their directory. Put that logic in your
    own app instead, in a module named for what it does (e.g.
    `<module_name>/integrations/sales_order_sync.py`), and call it from your
    hook.
- Name files and variables after what they represent, not how they're used —
  e.g. `operation_card_utils.py` not `helpers.py` or `misc.py`;
  `apply_status` not `do_thing`.

## Common patterns

### Set defaults before validation
````python
def before_validate(self):
    if not self.currency:
        self.currency = frappe.defaults.get_global_default("currency")
````

### Throw validation errors
````python
frappe.throw("Error message")                    # general error
frappe.throw("Message", frappe.ValidationError)  # with exception type
````

### Access current user
````python
frappe.session.user  # email of logged-in user
````

### Set field values
````python
def before_save(self):
    self.full_name = f"{self.first_name} {self.last_name}"
````

### Interact with other DocTypes
````python
def on_submit(self):
    frappe.get_doc(
        doctype="Notification Log",
        subject=f"Expense {self.name} approved"
    ).insert(ignore_permissions=True)
````

### Access flags
````python
# Set a flag to skip validation in specific cases
doc.flags.ignore_validate = True
doc.save()
````

## Anti-patterns

- **Don't use `frappe.db.set_value` for fields with validation logic.** It bypasses `validate()`, `before_save()`, and all lifecycle hooks. Never use it for status fields or state transitions. Use it only for simple counters, timestamps, or cached values.
````python
  # BAD — skips controller validation
  frappe.db.set_value("Expense", name, "status", "Approved")
  # GOOD
  doc = frappe.get_doc("Expense", name)
  doc.status = "Approved"
  doc.save()
````
- **Don't call `frappe.db.commit()` in controller methods or request handlers.** See the Transactions section in [database](./database.md) reference.
- **Don't write business logic directly in `<doctype_name>.py` hooks.** Hook methods should call a function, not implement the behavior — see File structure above.
````python
  # BAD — logic inline in the hook
  def validate(self):
      if self.amount > 10000 and not self.approver:
          frappe.throw("Approver required for amounts over 10,000")
      self.tax = self.amount * frappe.db.get_single_value("Tax Settings", "rate")

  # GOOD — hook delegates
  def validate(self):
      validate_approval_requirement(self)
      self.tax = calculate_tax(self.amount)
````
- **Put permission checks inside controller methods**, not in API wrapper helpers. This ensures enforcement regardless of call path (API, desk, background job). The controller method itself stays plain (non-whitelisted); the client-facing entry point is a separate thin wrapper under `<module_name>/api/`.
````python
  # BAD — check in api.py wrapper only; controller method has no enforcement
  # of its own, so anything calling the controller method directly (desk,
  # background job, another controller) skips the check entirely
  def _get_manager_doc(name):
      if "Expense Manager" not in frappe.get_roles(): ...

  # GOOD — check lives in the controller method itself (plain, not whitelisted)
  class Expense(Document):
      def approve(self):
          if "Expense Manager" not in frappe.get_roles():
              frappe.throw("Not allowed", frappe.PermissionError)
          self.status = "Approved"
          self.save()
````
````python
  # apps/<app>/<app>/<module>/api/v1/expense.py — thin wrapper, this is
  # what's actually @frappe.whitelist()-decorated and reachable from the client
  import frappe
  from <app_name>.<module_name>.doctype.expense.expense import Expense

  @frappe.whitelist(methods=["POST"])
  def approve_expense(expense_id: str):
      """
      Approve an expense, enforcing the Expense Manager role check defined
      on the controller.

      **Endpoint:** `/api/method/<app_name>.<module_name>.api.v1.expense.approve_expense`
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
      doc = frappe.get_doc("Expense", expense_id)
      doc.approve()
      return {"status": doc.status}
````
- **Be consistent with permission checks across all controller methods.** If some methods on a DocType check for a role explicitly, all mutating methods should do the same — don't rely on implicit DocType perms for some and explicit checks for others.