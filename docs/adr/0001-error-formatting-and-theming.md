# Error formatting and optional Rich theming

**Status:** accepted

## Context

`cli-error` unifies error reporting across CLI tools. Errors must be colorable
consistently, but coloring must be optional per project, and interpolating
untrusted values (paths, branch names, arbitrary input) into styled messages
must not be able to break or inject terminal markup.

## Decision

- **Named style roles as Rich markup.** Semantic coloring is expressed as Rich
  markup tokens (`[id]`, `[data]`, `[path]`, `[cmd]`, `[misc]`, `[warn]`,
  `[err]`) resolved by a Rich `Theme` the consumer chooses to apply — not by
  helper functions like `fmt_ident()`. The theme is built by merging a caller's
  overrides onto `DEFAULT_STYLES` (via `make_console`).
- **The theme is optional; Rich is not.** Rich is a hard dependency (already
  transitively required by Typer). A project that never applies the theme still
  works: undefined tokens render as plain text with no exception, even on a
  color terminal.
- **Format-template + escaped args.** Every trusted-markup surface — a `CliError`
  message, a `CliError.hint`, and a `CliExit` message — is a template whose markup
  is authored by the developer; dynamic values are passed as arguments and escaped
  before substitution, so untrusted data is safe by default. A single shared helper
  owns this substitution: arg-free calls store the template verbatim (literal
  `{...}` braces need no escaping), and any arg switches the template into
  `str.format` mode with each value `escape(str(value))`-substituted. Values
  interpolated inline (not passed as args) are the caller's responsibility to
  escape.
- **Fluent, typed builder for context.** Context is attached via chained
  methods: a markup-first `prop`, per-role helpers (`prop_id`, `prop_path`,
  `prop_data`, `prop_cmd`, `prop_misc`), a `hint`, and a keyless `detail` block.
  `prop(key, template, **args)` is the primary method and follows the same
  format-template + escaped-args rule as the message and `hint` (template is
  trusted developer markup; args are `escape(str(value))`-substituted; arg-free
  templates are stored verbatim). The per-role helpers are thin wrappers that
  wrap the value in their role's markup and pass it as an escaped arg
  (e.g. `prop_id(key, value)` ≈ `prop(key, "[id]{value}[/id]", value=value)`),
  keeping untrusted values safe by default. Prop values are resolved into
  role-wrapped markup immediately at construction rather than deferred to the
  render seam, so a prop is stored as `(key, resolved_markup)` with no separate
  role field.

## Considered options

- **Helper functions** (`fmt_ident(x)`, as in the source project) — rejected:
  boilerplate at every raise site and coloring baked into the exception.
- **Manual escaping with plain markup everywhere** — rejected: every untrusted
  interpolation is a foot-gun the caller must remember.
- **A custom markup/parse layer owned by the library** — rejected: reinvents
  Rich's parser, diverges from what Rich users know, and is the most code to own
  for no real gain.

## Consequences

- Migrating a consumer means dropping the `fmt_*` wrapping at each raise site and
  moving untrusted values into template args or typed `prop_*` calls — a
  mechanical simplification.
- One place (`CliReporter`) owns the render layout, so formatting stays uniform
  across every tool that adopts the library.
- Extending the format-template + escaped-args model to `CliExit` supersedes the
  `s01t01` decision that "`CliExit` is just an exception storing a plain
  (markup-capable) message." `CliExit` now accepts the same `(template, **args)`
  contract as `CliError`, with untrusted args escaped by the shared helper.
- Making `prop` markup-first supersedes the earlier "each method escapes its
  value and applies the role style at the render seam" wording. Roles are no
  longer carried as a deferred mechanism: props resolve to role-wrapped markup at
  construction, so there is no `role` field to interpret at render time and the
  render seam consumes ready-to-print markup. A later `prop` call for the same
  key overwrites the earlier one (last-wins).
