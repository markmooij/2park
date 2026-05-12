## Plan Review: Step 2 — Add `/health/scraper` Endpoint to `api.py`

### Verdict: APPROVE

### Summary
The plan is well-aligned with the PROMPT requirements and the existing `api.py` patterns. `scraper_health_check()` from Step 1 is already implemented and returns a clean dict, so the endpoint wiring is straightforward. The plan correctly identifies the key outcomes: HTTP 200 for both `"ok"` and `"degraded"` statuses, response time inclusion (already provided by the scraper method), and updating the root `/` docs. No blocking issues.

### Issues Found
_None blocking._

### Suggestions

- **Authentication:** The existing `/health` endpoint requires no auth token and no rate limiting — it is an unauthenticated probe. The plan is silent on whether `/health/scraper` should follow the same pattern. Given that the scraper health check navigates the live 2park.nl site with real credentials, it should probably either (a) require auth to prevent abuse or (b) be rate-limited independently. The PROMPT doesn't mandate auth on health endpoints, but the implementation should consciously decide — adding a `Depends(verify_token)` is the safest default given the scraper uses real credentials.

- **Timeout:** The plan says "add appropriate error handling and timeouts" but doesn't specify the timeout value. The scraper's `scraper_health_check()` already does a full login + navigation which can take 10–30 s. A top-level `asyncio.wait_for()` guard (e.g. 60 s) in the endpoint handler would prevent the request from hanging indefinitely if the scraper blocks. Worth having explicitly in the implementation even if not detailed in the plan.

- **`"degraded"` vs `"missing_selectors"` caveat from R002:** I flagged in the Step 1 code review that card-level selectors (`.parkapp-item`, `.extend-context-menu-button`, etc.) will always be absent when the account has no active bookings, making the status `"degraded"` spuriously. This will show up in the Step 2 endpoint response. The plan doesn't need to re-fix Step 1 work, but the worker should be aware that the endpoint may return `"degraded"` in a healthy empty state — worth noting in the endpoint's docstring or README.

- **Response model:** The existing endpoints use Pydantic `response_model=` declarations. `/health/scraper` returning a free-form dict is consistent with `/health`, so no Pydantic model is strictly needed — but declaring the response shape (even inline as a `dict` return annotation) would align with the project's FastAPI pattern.
