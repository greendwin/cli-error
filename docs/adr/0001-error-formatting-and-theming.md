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
- **Format-template + escaped args.** A `CliError` message is a trusted template
  whose markup is authored by the developer; dynamic values are passed as
  arguments and escaped before substitution, so untrusted data is safe by
  default. Values interpolated inline (not passed as args) are the caller's
  responsibility to escape.
- **Fluent, typed builder for context.** Context is attached via chained,
  per-role methods (`prop_id`, `prop_path`, `prop_data`, `prop_cmd`,
  `prop_misc`), a role-less `prop`, a `hint`, and a keyless `detail` block. Each
  method escapes its value and applies the role style at the render seam, so
  raise sites carry no manual escaping or styling.

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
- One place (`ErrorReporter`) owns the render layout, so formatting stays uniform
  across every tool that adopts the library.
