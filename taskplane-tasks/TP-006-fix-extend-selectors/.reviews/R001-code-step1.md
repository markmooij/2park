## Code Review: Step 1 — Rewrite `extend_booking()` with Correct Selectors

### Verdict: APPROVE

### Summary
The rewrite correctly replaces all placeholder selectors with the real selectors confirmed by the TP-003 DOM audit: `.parkapp-item`, `.license-plate.active`, `.extend-context-menu-button`, and `.time-container > .time > div` are all present in DOM_REFERENCE.md. The new end time is read back from the live page, falling back to a calculated value only when parsing fails. All 17 unit tests pass and syntax is clean.

### Issues Found
None blocking.

### Pattern Violations
None.

### Test Gaps
- The extend form UI (the modal/panel that appears after clicking "Verleng") was not captured in the DOM audit. All form-interaction selectors (`duration_selectors`, `submit_selectors`) are speculative. This is not a regression — the old code was also speculative — but end-to-end coverage of the happy path is not possible until Step 3 live testing.

### Suggestions

1. **`button:has-text("Verleng")` in `submit_selectors` could re-click the extend button.** After clicking `.extend-context-menu-button`, the original "Verleng" button is still in the DOM. If the extend form has no `button[type="submit"]`, the selector `button:has-text("Verleng")` would match the extend button again, not the form's confirm button. Consider scoping the submit-button search to within the newly-opened dialog/modal, or moving `button:has-text("Verleng")` to after the more specific Dutch-verb alternatives (`Bevestigen`, `Opslaan`). Not blocking — the form's actual structure will be verified in Step 3.

2. **Type inconsistency in `new_end_time`.** `parse_dutch_time()` returns `str` (ISO string); the fallback at line 927 returns a `datetime`. Both are accepted by Pydantic's coercion, so there's no runtime failure, but the variable holds different types on different code paths. Consider wrapping the `parse_dutch_time()` result with `date_parser.isoparse(...)` to always return `datetime`, matching the fallback path.

3. **`from datetime import timezone as tz` inside a loop (line 912).** This import is in an inner `try` block. `timezone` is already imported at the top of the module. Replace with the already-imported `timezone` alias and remove the redundant import.

4. **`button[type="button"]` as last-resort submit selector** is very broad and would match any generic button (e.g. "Cancel", "Terug"). If the extend form renders a cancel button before a confirm button, this could submit the wrong action. Not blocking given it's the last fallback, but worth noting for Step 2 hardening.
