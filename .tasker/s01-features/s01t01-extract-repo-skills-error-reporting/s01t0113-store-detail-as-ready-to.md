---
id: s01t0113
slug: store-detail-as-ready-to
status: done
---

# Store detail as ready-to-print [misc] markup (restore render-seam invariant)

## Goal

Restore ADR-0001's "the render seam consumes ready-to-print markup" invariant for the detail block. Currently `CliError.detail(text)` stores `_detail_text = escape(text)` (escaped only) and `render_error` wraps it as `[misc]{_detail_text}[/misc]` at print time — the one place the reporter still injects a role token (props/message/hint all print stored markup verbatim).

## Change

- `CliError.detail`: store the ready-to-print markup at construction — `self._detail_text = f"[misc]{escape(text)}[/misc]"` (escape first, then wrap; rendered output is byte-identical).
- `render_error` (`src/cli_error/_reporter.py`): print `ex._detail_text` verbatim, matching how it already prints props — remove the `[misc]` wrapping from the reporter.

## Why out of s01t03's scope

Discovered as a delayed refactor finding during s01t03's dev-loop. It cannot be applied behavior-preserving within the render slice because tests owned by the detail-storage slice assert the RAW stored field:

- `tests/test_errors.py::test_detail_is_escaped_at_store` — asserts `_detail_text == escape("a[b]c")`
- `tests/test_errors.py::test_detail_last_wins` — asserts `_detail_text == escape(...)`
- `tests/test_errors.py::test_arbitrary_chaining_order_works` — asserts `_detail_text == "d"`

These expected values must change to the `[misc]`-wrapped form (e.g. `f"[misc]{escape('a[b]c')}[/misc]"`). That crosses into the detail-storage contract, so it belongs in its own task.

## Acceptance criteria

- `CliError.detail` stores `[misc]`-wrapped, escaped markup; `render_error` no longer injects `[misc]`.
- The three `test_errors.py` assertions above are updated to expect the `[misc]`-wrapped stored value; all render-output assertions in `tests/test_render.py` remain unchanged (output is byte-identical).
- No other reader of `_detail_text` expects un-wrapped text (grep to confirm).
- `uv run tox` is green.
