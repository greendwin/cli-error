---
id: s01t17
slug: test-debug-traceback-includes-the
status: pending
---

# Test: debug traceback includes the exception cause chain

## Context

Follow-up from s01t06 (Debug traceback). Surfaced by the `tests` code-review lens.

The debug traceback for a chained exception (`raise X from Y`) is a plausible public expectation, especially given the repo already renders a cause chain in the stdout `Error:` line. The current debug tests only assert `"Traceback"` and the top exception type appear on stderr; no test covers that the emitted traceback includes the full cause chain. Low priority — `Console.print_exception()` cause-chain rendering is Rich-owned behavior.

## Possible approach

Add a behavior-level test that, with `debug=True`, raises an exception with a `from` cause through the handler and asserts both the outer and the cause type names appear in the captured stderr — confirming the full chain is emitted rather than just the top frame.

## Acceptance criteria

- Test raises a chained exception (`raise Outer(...) from Inner(...)`) under `debug=True` and asserts both type names appear in captured stderr.
- `uv run tox` green.
