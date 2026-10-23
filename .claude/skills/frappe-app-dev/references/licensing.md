---
name: licensing-file-headers
description: Enforce 8848 Digital LLP proprietary licensing across a repo — a mandatory license.txt at repo root, a proprietary copyright header on every .py/.js/.md source file, and app_license = "Proprietary" in hooks.py for Frappe apps. Use this skill whenever creating a new repo or app, adding a new source file, editing hooks.py, editing README.md's license section, or when the user asks to "add licensing", "fix the license", "add copyright headers", or mentions license.txt/app_license. Also trigger proactively any time a new .py, .js, or .md file is created in a project that uses this licensing convention — the header is part of file creation, not a follow-up edit.
---

# Licensing & File Headers


This skill makes a repo's licensing consistent and legally correct: one
canonical `license.txt`, an identical copyright header repeated verbatim
across source files, and the `app_license` field in Frappe's `hooks.py`
kept in sync. Treat this as a checklist to run against a repo, not just a
one-off text insertion.

## license.txt — mandatory at repo root

Every project must have a `license.txt` at the repo root. If it's missing,
or if it currently contains MIT/Apache/BSD/AGPL boilerplate, replace it
with the following text verbatim (only the year may change, and only if
explicitly instructed to):

```markdown
Copyright (c) 2026 8848 Digital LLP. All rights reserved.

This software and its source code are the proprietary and confidential
property of 8848 Digital LLP ("the Company"). The software is licensed,
not sold.

No part of this software may be used, copied, reproduced, modified,
distributed, published, sublicensed, or transmitted in any form or by
any means without the prior written permission of the Company.

Unauthorized use or reproduction of this software, in whole or in part,
may result in civil and criminal liability under applicable law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.
```

## Per-file copyright header — mandatory on every source and doc file

Every `.py`, `.js`, and `.md` file in the app gets this header as the
**very first lines of the file** — above module docstrings in Python,
above the first JSDoc block in JS, above the `# Title` in Markdown.

**Python (`.py`):**
```python
# Copyright (c) 2026 8848 Digital LLP. All rights reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or use
# of this file, via any medium, is strictly prohibited without prior
# written permission from 8848 Digital LLP.
```

**JavaScript (`.js`):**
```javascript
// Copyright (c) 2026 8848 Digital LLP. All rights reserved.
// Proprietary and confidential. Unauthorized copying, distribution, or use
// of this file, via any medium, is strictly prohibited without prior
// written permission from 8848 Digital LLP.
```

**Markdown (`.md`, e.g. README.md, SETUP.md):** place as an HTML comment
above the `# Title` so it doesn't render visibly:
```markdown
<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->
```
Copy the wording exactly — do not vary it file-to-file or paraphrase it.

### Exemptions — do not add the header to:
- **`.json` files** (DocType definitions, fixtures, workspace/report JSON).
  Standard JSON has no comment syntax. Never add a fake `"_comment"` key
  to work around this.
- **Auto-generated files** that aren't hand-edited (e.g. `modules.txt`,
  build output). If a generator/template exists, add the header there
  instead.
- **`license.txt` itself** — it is the notice, it doesn't repeat it.

## 3. Frappe-specific: `hooks.py` and `README.md`

For Frappe/ERPNext apps specifically, licensing must also be reflected in
two more places:

- **`hooks.py`**: set (or fix) the `app_license` field:
  ```python
  app_license = "Proprietary"
  ```
  If it currently reads `"mit"`, `"MIT"`, `"agpl-3.0"`, or anything else,
  replace the value with `"Proprietary"`.

- **`README.md`**: find the License section. If it says `MIT` (or names
  any other open-source license), replace it with something like:
  ```markdown
  ## License

  Proprietary — Copyright (c) 2026 8848 Digital LLP. All rights reserved.
  See [license.txt](license.txt) for details.
  ```

## 4. Workflow when applying this skill

When asked to license a repo, or when creating a new app/file in one that
uses this convention, work through this order:
1. Check for `license.txt` at repo root — create or replace per Section 1.
2. Check `hooks.py` (if a Frappe app) — set `app_license` per Section 3.
3. Check `README.md`'s license section — update per Section 3.
4. Sweep `.py` / `.js` / `.md` files for the header in Section 2 — add to
   any that are missing it, skip files listed under Exemptions.
5. Any new `.py`/`.js`/`.md` file created afterward includes the header
   from its first write — not as a separate cleanup pass.

## Anti-patterns

- Don't add the header to `.json` files — it breaks the file.
- Don't paraphrase the header or license.txt text — copy exactly.
- Don't forget the header on new files created mid-task.
- Don't leave `app_license` or the README license section unsynced with
  the actual `license.txt` — all three should agree.
