## Plan Review: Step 1 — Add `scraper_health_check()` to `TwoParkScraper`

### Verdict: APPROVE

### Summary
The plan is clear and well-scoped. The method signature, return shape, and the
selectors to check all align with what's in DOM_REFERENCE.md and the existing
scraper patterns. The approach of reusing `_find_booking_card()` navigation
patterns (navigate to dashboard, check tabs, check `.parkapp-item`) is sound
and consistent with how TP-007 built the shared helper.

No blocking issues. A couple of minor observations below.

### Issues Found
*(None blocking)*

### Pattern Violations
*(None)*

### Test Gaps
*(None for this step — testing is Step 4)*

### Suggestions

- **Selector accuracy:** PROMPT.md says check `.tabText` — DOM_REFERENCE.md
  confirms `.tabText` is the span inside each tab button. Also confirm
  `.tabs-container` and `.tabs` are both present. The DOM audit shows the
  `"Lopend"` tab button has class `active`, so the worker should check for
  `.tabs-container` existence rather than assuming `button.active` is always
  present (it changes based on selected tab).

- **No-bookings edge case:** The PROMPT says "even if no cards, the container
  should be there". The DOM shows `.list-container` / `.site-list-content` as
  the outer wrapper, but there's no explicit empty-state selector documented.
  The worker should clarify which container they expect to always exist even
  when the booking list is empty (`.tabs-container` is always rendered; the
  `.parkapp-item` check should be "container exists", not "at least one item").
  This is a judgment call, not a blocker — the PROMPT already calls it out.

- **Return type `dict`:** Consider whether to add a TypedDict or at minimum
  document the dict keys in a docstring so Step 2's endpoint implementation
  doesn't have to guess the shape. Minor but saves a round-trip.

- **Timeout handling:** The method will call `_login()` implicitly via
  `initialize()` (it's a context-manager method). A `PlaywrightTimeoutError`
  should be caught and returned as `{"status": "degraded", ...}` rather than
  propagating an unhandled exception — consistent with the "don't fail the
  health check entirely" policy stated in Step 2.
