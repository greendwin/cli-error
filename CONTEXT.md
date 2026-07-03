# Glossary

| Term | Definition |
|------|-----------|
| **CliError** | The library's base application exception. Carries a message plus optional context props, a hint, and detail blocks, all formatted for terminal display. Its message is a **format template** (see below); consuming CLI tools subclass it for their own error kinds. |
| **Format template** | An error message string that mixes trusted style markup (e.g. `[id]…[/id]`) with placeholders filled from arguments. Argument values are escaped before substitution, so untrusted data cannot inject or break markup. Values interpolated inline (not passed as arguments) are the caller's responsibility to escape. |
| **Context prop** | A `key: value` line of secondary context attached to an error. The value is escaped and styled by a chosen style role; the key renders plain. Rendered indented beneath the error message. |
| **Hint** | An optional suggestion appended to an error after a blank line, telling the user how to fix it. May contain style markup. |
| **Detail block** | A keyless block of raw text attached to an error (e.g. captured subprocess output). Escaped, styled `misc`, and rendered on its own line(s) with no `key:` prefix. |
| **CliExit** | A control-flow exception signalling a clean exit — "nothing to do, this is not a failure". Caught by the error handler, which prints its (markup-capable) message and exits with status `0`. Used for shortcuts like `--version` or "no results". |
| **ErrorReporter** | The single integration point a CLI tool constructs once in `main()`. Built from a themed console, it owns the `--debug` flag, renders errors (`[err]Error:[/err] …` plus the cause chain), prints full tracebacks to its own themed stderr console when `debug` is set, and exposes the error-handling context manager. |
| **Console factory** | A helper that builds a Rich console pre-loaded with the library's theme and sensible defaults. The consumer owns the resulting console; the library keeps no global singleton. |
| **Theme** | The optional Rich theme mapping semantic style roles to colors. Applying it lets a project write markup like `[id]main[/id]` instead of calling helper functions. A project that does not apply it still runs — the role tokens degrade to unstyled text. |
| **Style role** | A named semantic color in the Theme. The canonical roles are `id` (identifier, green), `data` (requested value, cyan), `path` (filesystem path, dim), `cmd` (command/flag to run, blue), `misc` (additional detail, dim), `warn` (warning prefix, yellow), `err` (error prefix, red). Roles are distinct even when they share a default color; a consumer may override any mapping. |
