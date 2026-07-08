---
id: s01t0120
slug: add-a-safe-post-construction
status: done
---

# Add a safe post-construction debug toggle to CliReporter

## Context

Follow-up from s01t18. `CliReporter` gained a `debug(template, ...)` method, which forced the debug **flag** to become private (`self._debug`) — a public `debug` attribute would shadow the `debug()` method. As a result there is no supported way to enable debug diagnostics after construction; only the `debug=` constructor arg works.

This is a latent footgun: a consumer following the pre-s01t18 guidance `reporter.debug = True` (still present in historical task records and the not-yet-written s01t08 README) silently rebinds the `debug()` method to a bool. The assignment succeeds, the real gate `self._debug` stays `False`, every diagnostic is silently suppressed, and any later `reporter.debug("...")` call raises `TypeError: 'bool' object is not callable`. No error surfaces at the assignment site.

## Decision

- **Add an explicit safe toggle** to enable/disable debug after construction, e.g. `enable_debug(value: bool = True)` or `set_debug(value: bool)` returning `None`. A `property` named `debug` cannot be used — it collides with the `debug()` method — so the toggle must have a distinct name.
- Keep the `debug=` constructor arg and the private `self._debug` gate as the single source of truth; the toggle just writes it.
- Align documentation to the construction-time-or-toggle model: update the s01t08 README guidance (when written) and any other consumer-facing docs to stop instructing `reporter.debug = True`. Historical `.tasker/**` task records are immutable history — do not edit.

## Acceptance criteria

- A public method enables/disables debug after construction and correctly gates `debug`, `debug_traceback`, `debug_cmd`, `debug_output`.
- Behavior-level tests: toggling on after construction makes a previously-silent `debug(...)` emit; toggling off silences it.
- Consumer-facing docs describe the toggle, not attribute assignment.
- Consider ADR 0002 (constructor-oriented gating) and coordinate with s01t15/s01t16 (debug console intent / show_locals) so the toggle story stays coherent.
- `uv run tox` green.

## Out of scope

- Reintroducing a public mutable `debug` attribute (impossible without shadowing the method).
