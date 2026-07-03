---
id: s01t12
slug: revisit-props-markup-first-prop
status: pending
---

# Revisit props: markup-first `prop` with template+args, roles as thin helpers

## Goal

Revisit the context-prop design. Today a prop stores an escaped value plus a
`Role`, and the role's style is applied later "at the render seam" (deferred
markup). Reconsider whether that deferral — and the `Role` mechanism itself — is
needed, and give the developer direct markup control over prop values.

## Open questions / direction

- **Do we need `Role` at all?** The role exists to *delay* markup application to
  the render seam. But we can always apply markup *immediately* at construction —
  resolve the value into role-wrapped markup text right away — which may remove
  the need to carry a `Role` (and the `role` field on `_Prop`) through to
  rendering. Decide whether `_Prop` collapses to just `(key, resolved_markup)`.
- **A markup-first `prop(key, template, **args)`.** Make `prop` the primary
  method for assigning marked-up text, using the same trusted-template +
  escaped-args rule as `message` / `hint` / `CliExit` (template is developer
  markup; args are `escape(str(value))`-substituted). This is where template+args
  gives the developer control.
- **`prop_xxx` become tiny helpers for common patterns.** `prop_id`,
  `prop_path`, `prop_data`, `prop_cmd`, `prop_misc` reduce to thin wrappers over
  `prop` that wrap the value in their role's markup for the common case
  (e.g. `prop_id(key, value)` ≈ `prop(key, "[id]{v}[/id]", v=value)`), keeping
  the safe-by-default escaping for plain values.

## Constraints & considerations

- **Safety:** the template+args rule keeps untrusted args escaped; the `prop_xxx`
  helpers must keep untrusted values escaped by default (pass them as args, not
  verbatim) so no injection regression versus today's auto-escaping props.
- Props rendering is not yet implemented — resolve this design before/with the
  renderer so the render seam matches the chosen `_Prop` shape.
- Relates to s01t10's markup-construction rule (`(template, **args)` = "markup
  here") and the shared `_resolve` helper — the `prop` method should reuse it.

## Docs to amend

- `docs/adr/0001-error-formatting-and-theming.md` — update the "Fluent, typed
  builder for context" decision and the "escapes its value and applies the role
  style at the render seam" wording to reflect markup-first props (and, if roles
  are dropped as a deferred mechanism, record that supersession with rationale).
- `CONTEXT.md` — update the **Context prop** / **Style role** glossary entries if
  the role mechanism changes.

## Acceptance criteria (draft — refine when picked up)

- `prop(key, template, **args)` assigns marked-up text via the shared template+args
  helper (args escaped, arg-free verbatim).
- `prop_xxx` are thin helpers over `prop` preserving safe-by-default escaping of
  plain values.
- Decision recorded on whether `Role`/deferred-render is kept or dropped, with
  `_Prop` shape updated accordingly.
- ADR-0001 (and CONTEXT.md if affected) amended.
- `uv run tox` green.
