# General — Context

**Last Updated:** 2026-05-08
**Status:** Active
**Next Task ID:** TP-010

---

## Current State

This is the default task area for 2park. Tasks that don't belong
to a specific domain area are created here.

Taskplane is configured and ready for task execution. Use `/orch all` for
parallel batch execution or `/orch <path/to/PROMPT.md>` for a single task.

---

## Key Files

| Category | Path |
|----------|------|
| Tasks | `taskplane-tasks/` |
| Config | `.pi/taskplane-config.json` |

---

## Technical Debt / Future Work

### TP-001 Discrepancy Fixes (2026-05-08)

Three discrepancies discovered during TP-001 end-to-end test:

1. **License plate normalization** — API returns `51-PX-PN` but website stores `51PXPN`. Fixed by TP-004.
2. **Booking duration discrepancy** — API calculates end time locally but website uses its own logic. Fixed by TP-005.
3. **Scraper selector mismatch** — `extend_booking()` uses placeholder selectors not present in live DOM. Fixed by TP-006, TP-007, TP-008.

### Task Dependency Chain

```
TP-003 (DOM audit) → TP-004 (license normalization)
                   → TP-005 (actual end time)
                   → TP-006 (fix extend selectors) → TP-007 (shared helper) → TP-008 (health check)
```

_Items discovered during task execution are logged here by agents._
