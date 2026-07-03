---
id: s01t14
slug: handle-empty-message-cause-in
status: pending
---

# Handle empty-message cause in cause-chain rendering

## Goal\n\nDecide and implement how `render_error`'s cause-chain walk (`_cause_chain`/`print_error` in `src/cli_error/_errors.py`) renders a cause whose `str()` is empty (e.g. `ValueError()`).\n\n## Context\n\nCurrently such a cause produces `  caused by: ` — a line with a trailing space and no content. Surfaced as a `nit` by the `thermo-nuclear` and `general` review lenses during dev-loop of s01t05 (cause-chain rendering). Deferred because changing it alters observable output, so it needs a deliberate product decision plus its own test rather than a behavior-preserving refactor.\n\n## Options to weigh\n\n- Skip the link entirely when `str(cause)` is empty.\n- Strip the trailing space (render `  caused by:`).\n- Fall back to the exception's type name (e.g. `caused by: ValueError`).\n\n## Acceptance criteria\n\n- Chosen behavior implemented in `print_error`/`_cause_chain`.\n- A behavior-level test in `tests/test_render.py` pins the output for an empty-message cause.\n- `uv run tox` green.
