---
id: s01t17
slug: test-debug-traceback-includes-the
status: done
---

# Test: debug traceback includes the exception cause chain

## Context

Follow-up from s01t06. The debug traceback comes from Rich's `print_exception()`, which walks `__cause__`/`__context__` itself. Existing debug tests only assert `"Traceback"` and the top exception type on stderr; no test covers that a chained exception (`raise X from Y`) emits the full chain — a plausible public expectation, especially since the repo already renders a cause chain in the stdout `Error:` line. Low priority (cause-chain rendering is Rich-owned), so this is test-only.

## Decisions

- **Drive it through `handler()` end-to-end** — raise `Outer("...") from Inner("...")` inside `reporter.handler()` with `debug=True`, assert both `"Outer"` and `"Inner"` type names appear in captured stderr. Covers the path users actually hit (automatic emission on an unhandled error) and reuses the `run_handler` idiom in `test_reporter.py`. *Rejected: calling `debug_traceback()` directly in an `except` block — that path is already exercised by s01t18's helper tests.*

## Edge cases

- Assert on **type names** (`Outer`/`Inner`), which appear regardless of Rich's exact traceback formatting, rather than on brittle layout text.

## Key files

- `tests/test_reporter.py` — new test using the existing `run_handler` helper (or the s01t19 shared `capture`).

## Acceptance criteria

- A test raises `raise Outer(...) from Inner(...)` under `debug=True` through `handler()` and asserts both type names appear in captured stderr.
- `uv run tox` green.

## Out of scope

- Non-test behavior changes.
