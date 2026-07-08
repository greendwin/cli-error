---
id: s01t21
slug: reconsider-debug-output-layout-evaluate
status: done
---

# Reconsider debug_output layout — rule/divider delimiters

**Superseded by s01t22:** the `─── stdout ───` rule layout below is replaced by the uppercase `LABEL:` header idiom (`STDOUT:` / `STDERR:` header line followed by the captured block).

`src/cli_error/_reporter.py` · `debug_output()`:
> TODO: this layout is ugly, lets prepend each line 'stdout: ' prefix

The current layout emits a `  stdout:` / `  stderr:` header line followed by the captured text as one escaped `misc` block. The body sits flush at column 0, so it has no visual boundary and merges with surrounding debug output.

**Decision:** Adopt the **rule/divider** layout (variant B). Each non-empty stream is delimited by a labeled `misc`-styled rule above the captured block:

```
─── stdout ───
line1
line2
─── stderr ───
err1
```

This labels each stream once (no per-line prefix), so it does not reopen the objection s01t18 named when it **rejected** per-line prefixing: *"bloats multi-line logs"*.

**Requirements:**
- A stream's rule is emitted **only when that stream is non-empty** — the existing empty/whitespace-only skip (`rstrip` → `continue`) must still apply, so an empty `stderr` produces no `stderr` rule at all.
- Keep the captured text as one escaped `misc` block (internal newlines preserved, trailing whitespace `rstrip`ped) — same escaped-arg contract as today.
- The rule/label styling routes through the existing `misc` role like the rest of the debug helpers.

Remove the TODO in `debug_output` once implemented.
