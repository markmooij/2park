## Code Review: Step 3 — Add `SELECTOR_MISMATCH` Error Code

### Verdict: APPROVE

### Summary
The change is minimal and correct: `SELECTOR_MISMATCH` is added to the `ErrorCode` enum in the `Scraping errors` group alongside its peers (`SCRAPE_ERROR`, `TIMEOUT_ERROR`, `ELEMENT_NOT_FOUND`), and a `SelectorMismatchException` class is created following the exact same pattern as every other exception in the file. The class is importable, instantiates cleanly with and without arguments, and is wired to the correct error code and HTTP 500 status. Python compilation and import checks pass cleanly.

One observation: `SelectorMismatchException` is defined but not yet used by `scraper.py` or `api.py` — those callers return `"degraded"` status dicts rather than raising. This is intentional per the PROMPT (Step 2 specifies HTTP 200 / degraded, not an exception). The class exists for future callers that need to surface a hard failure. No action required.

### Issues Found
*None*

### Pattern Violations
*None — class structure, constructor signature, and `super().__init__()` call are consistent with every other exception in the file.*

### Test Gaps
- No unit test for `SelectorMismatchException` instantiation (default args, with `missing_selectors`). Not blocking — the class is trivially correct and the exception is not yet exercised by the endpoint, so there is nothing to test at the integration level either. Can be added when the exception is first raised in production paths.

### Suggestions
- The `details` dict passed to `APIException.__init__` (containing `missing_selectors`) is stored on `self.details` but not surfaced by `to_response()`. This means if the exception is ever raised and caught by the FastAPI `api_exception_handler`, the `missing_selectors` list is silently dropped from the HTTP response body. Consider extending `to_response()` to include `details` when non-empty, or document that callers should extract `self.details` themselves. This is pre-existing behaviour (not introduced here), so it's a suggestion rather than a blocker.
