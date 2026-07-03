---
id: s01t11
slug: refine-detail-single-last-wins
status: pending
---

# Refine detail — single last-wins str block

## Goal

Make `detail` a single last-wins block (symmetric with `hint`) and retype it `str`, resolving two design TODOs left in `s01t02`.

## Notes captured (verbatim TODOs)

`src/cli_error/_errors.py` · `CliError.hint()` / `detail()`:
> # TODO: why hint replaces prev val, but `detail` appends?

`src/cli_error/_errors.py` · `CliError.detail()`:
> # TODO: do we need `Any`? why not str?

## Decisions & constraints

- **Collapse `details` list → single last-wins block.** The append/list semantics introduced in `s01t02` has no driving use case: the original (`repo-skills`) only ever held one detail block via the `props[""]` dict hack (overwrite, never append), with a single call site (captured subprocess output). Symmetry with `hint` (also last-wins) removes the asymmetry the TODO flags. Storage becomes `detail_text: str | None` (or equivalent single slot), not a list.
- **Retype `detail(text: str)`** — a detail block is text by definition; drop the `str()` coercion. **Keep `escape()`** (markup safety — detail is an untrusted-value surface per the markup-construction rule). Contrast `prop_*` whose `Any` value is meaningful; `detail`'s `Any` was accidental symmetry.
- Adjust `s01t02`'s storage field and its tests to match (this changes already-landed `s01t02` behavior — land it as a forward task, not a reopen).

## Edge cases

- `detail` set twice — second call wins (assert last-wins, mirroring `hint`).
- `detail` with markup characters (`[`/`]`) — still escaped at store (unchanged).
- No `detail` set — renders/omits cleanly (baseline unchanged).

## Key files

- `src/cli_error/_errors.py` — single `detail` slot; `detail(text: str)` keeping `escape`, dropping `str()`. Remove both TODOs.
- `tests/test_errors.py` — replace append/order-of-details coverage with last-wins; drop the non-str stringify coverage for `detail` (keep it for `prop_*`).

## Acceptance criteria

- `detail` stores a single block; a second `detail(...)` replaces the first.
- `detail` signature is `str`; value is escaped at store; no `str()` coercion.
- Any `s01t02` tests asserting multiple detail blocks / detail stringify-`Any` are updated to the new semantics.
- Both TODO comments removed.
- `uv run tox` is green.
