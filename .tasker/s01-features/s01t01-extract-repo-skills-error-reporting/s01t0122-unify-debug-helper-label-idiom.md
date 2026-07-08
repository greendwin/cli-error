---
id: s01t0122
slug: unify-debug-helper-label-idiom
status: done
---

# Unify debug-helper label idiom (debug_cmd vs debug_output)

## Context

After s01t21 adopted a labeled rule/divider for `debug_output` (`─── stdout ───`), the two subprocess debug helpers in the reporter presented labels in two different visual idioms: `debug_output` used rule headings while `debug_cmd` used an indented `COMMAND:` / `  cwd:` header. A `--debug` dump commonly interleaves both helpers (a command followed by its captured output), so the two grammars sat side by side in one stderr stream. This task unifies them onto a single label grammar.

## Decisions

- **Unify on one uppercase `LABEL:` grammar (variant c)** — abandon the rule/divider entirely; every field is introduced by an all-uppercase, flush-left `LABEL:`. Scalars put the value inline (`RUN: git commit -m 'a b'`, `CWD: /tmp/x`); blocks put a bare header then the value on following lines (`STDOUT:` then the block). One grammar for the whole debug stream; each helper reads fine alone or back-to-back. *Rejected: (a) unifying toward the rule idiom `─── command ───` — a rule above a single-line command is visual noise, and a lonely `─── cwd ───` for one path is heavy; (b) keeping the two idioms distinct — the scalar-vs-block distinction is real but not worth making the reader parse two label grammars in one stream.*

- **Label set: `RUN:` / `CWD:` / `STDOUT:` / `STDERR:`** — all-uppercase, column 0, no indentation (drops the old `  cwd:` two-space indent). `RUN` over `COMMAND` (shorter; reads as "the command we ran"). Every line stays wrapped in `[misc]…[/misc]`; the `LABEL:` chars live in the trusted template and values (`cmd`, `cwd`, `text`) pass as escaped args — escaped-arg contract (ADR 0001) unchanged.

- **`debug_cmd`: two independent prints** — `RUN: {cmd}` always (via `shlex.join`), then `CWD: {cwd}` only when `cwd is not None`. Two separate `debug_print` calls because `CWD` is conditional. The helpers stay two fully independent methods — `debug_cmd` alone emits just `RUN:`/`CWD:`, `debug_output` alone emits just the stream blocks, and together they compose; no merging.

- **`debug_output`: header + block as one `[misc]` unit** — emit each non-empty stream as a single markup string `"[misc]STDOUT:\n{text}[/misc]"` (label and block coupled as one styled unit) rather than two prints. Empty-stream skip preserved unchanged: a stream's header is emitted only when non-empty (`rstrip()` → `continue`); body keeps internal newlines, `rstrip`s trailing whitespace, one escaped `misc` block.

- **s01t21 superseded on layout** — this task lands the final unified idiom across both helpers and replaces s01t21's `─── stdout ───` rule; s01t21 (in-review) gets a one-line supersede note pointing here rather than being reopened. *Note: this does NOT reopen the s01t18 objection that rejected per-line `stdout: ` prefixing for bloating multi-line logs — the format is a single header per stream, not a per-line prefix.*

## Edge cases

- `debug_cmd` with no `cwd` → only the `RUN:` line, no `CWD:` line.
- `debug_output` with one empty stream → only the non-empty stream's header+block; an empty/whitespace-only stream produces no header at all (existing `rstrip` → `continue`).
- Both streams empty/whitespace-only → nothing emitted.
- All helpers are silent no-ops when `debug` is unset.
- Markup in values (`[red]…[/red]`, brackets in a command arg) must render literally — escaped-arg contract holds for `cmd`, `cwd`, and `text`.
- `misc` styling must actually apply: with color forced on, the `[misc]` (=dim) ANSI escape must wrap `RUN:` and the `STDOUT:` header.
- Multi-line stdout with trailing blank lines → internal newlines preserved, trailing whitespace `rstrip`ped.

## Key files

- `src/cli_error/_reporter.py` — `debug_cmd()` (`COMMAND:`/`  cwd:` → `RUN:`/`CWD:`) and `debug_output()` (rule → `STDOUT:`/`STDERR:` header block); update `debug_output`'s docstring.
- `tests/test_reporter.py` — update assertions: `COMMAND:`→`RUN:`, `cwd:`→`CWD:`, `─── stdout ───`→`STDOUT:` (incl. the ordering assertions and the `misc`-style ANSI-escape tests).
- `.tasker/s01-extract-repo-skills-error-reporting/s01t21-reconsider-debug-output-layout-evaluate.md` — one-line supersede note.

## Acceptance criteria

- `debug_cmd(["git","commit","-m","a b"], cwd=Path("/tmp/x"))` under debug emits `RUN: git commit -m 'a b'` and `CWD: /tmp/x`; no `COMMAND:` or lowercase `cwd:`.
- `debug_cmd(["ls"])` emits `RUN: ls` and no `CWD:` line.
- `debug_output("out1\nout2  \n", "err1")` emits a `STDOUT:` header before `out1\nout2` and a `STDERR:` header before `err1`; no `─── … ───` rule, no lowercase `stdout:`/`stderr:`.
- `debug_output("kept", "   ")` emits `STDOUT:` + `kept` and no `STDERR:`.
- Markup-bearing values render literally (`[red]…[/red]` preserved) for both helpers.
- With color forced on, the dim `misc` ANSI escape wraps both `RUN:` and the `STDOUT:` header.
- All helpers stay silent when `debug` is unset.
- s01t21 file carries a supersede note pointing to s01t22.
- `uv run tox` green across all environments, including any pre-existing issues.

## Open questions

- None outstanding — all grill questions resolved.

## Out of scope

- No CONTEXT.md change — the "Debug diagnostic" glossary entry never pinned an idiom.
- No new ADR and no ADR 0002 edit — the idiom is cosmetic and trivially reversible (fails the "hard to reverse" bar), and ADR 0002 already describes these helpers as `misc`-styled escaped-arg wrappers without pinning a label style.
- Reworking `debug_output`'s empty-skip / escaping behavior — carried over unchanged from s01t21.
