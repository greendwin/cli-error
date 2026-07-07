Cli Error
=========

Error handling and reporting utilities for CLI applications.

`cli-error` is a small, framework-agnostic toolkit for command-line programs,
built on three things:

- **`CliError`** — one exception type whose message is a rich-formatted template,
  carrying bound context props and a hint. Raise structured errors instead of
  hand-formatting strings.
- **`CliReporter`** — one object you wire in `main()`. It centralizes terminal
  output, renders errors (including their cause chain) into clean text and exit
  codes, and catches `CliExit` for a graceful exit `0`.
- **debug helpers** — `debug_*` methods gated by a single `debug` flag that
  unify diagnostics — tracebacks, subprocess commands and their output — onto a
  stderr console you can sprinkle freely.

Coloring is optional [Rich](https://rich.readthedocs.io/) theming that degrades
gracefully to plain text when a project opts out.

## Install

`cli-error` targets **Python 3.12+**.
The import package is `cli_error`.

```bash
pip install cli-error
# or
uv add cli-error
```

```python
from cli_error import CliError, CliExit, CliReporter, escape, make_console
```

## `CliError` — rich, structured errors

`CliError(template, /, **args)` builds an error whose message is a markup
template. Every builder method returns the error, so calls chain:

```python
from cli_error import CliError

raise (
    CliError("cannot check out [id]{commit}[/id]", commit=commit)
    .prop_path("repo", repo_path)
    .prop_cmd("ran", "git checkout")
    .hint("fetch the branch first: [cmd]{cmd}[/cmd]", cmd="git fetch origin")
    .detail(stderr_text)
)
```

Builder surface:

| Method       | Signature                         | Effect                                      |
| ------------ | --------------------------------- | ------------------------------------------- |
| constructor  | `CliError(template, /, **args)`   | main one-line message                       |
| `.hint`      | `.hint(template, /, **args)`      | a follow-up suggestion line                 |
| `.detail`    | `.detail(text)`                   | a `misc`-styled detail block (text escaped) |
| `.prop`      | `.prop(key, template, /, **args)` | a labelled context property (markup-first)  |
| `.prop_id`   | `.prop_id(key, value)`            | property wrapped in `[id]…[/id]`            |
| `.prop_path` | `.prop_path(key, value)`          | property wrapped in `[path]…[/path]`        |
| `.prop_data` | `.prop_data(key, value)`          | property wrapped in `[data]…[/data]`        |
| `.prop_cmd`  | `.prop_cmd(key, value)`           | property wrapped in `[cmd]…[/cmd]`          |
| `.prop_misc` | `.prop_misc(key, value)`          | property wrapped in `[misc]…[/misc]`        |

`str(error)` returns the plain, markup-stripped one-line message (there is no
`.message` attribute on `CliError`):

```python
try:
    raise CliError("cannot read [id]{commit}[/id]", commit="a[b]c")
except CliError as error:
    print(str(error))  # cannot read a[b]c
```

**Template semantics.** With no args the template is stored verbatim (literal
`{...}` is kept). With args it is treated as a `str.format` string — each value
is `escape(str(value))`-substituted, so literal braces must be doubled (`{{`,
`}}`). Trusted markup tokens in the template are preserved; arg values can never
inject markup.

### Style roles

The markup tokens you write in templates — `[id]…[/id]`, `[warn]…[/warn]`, and
so on — are named *style roles*. Each maps to a default color; a project that
never applies the theme still runs fine, since unknown tokens degrade to plain
text.

| Role   | Default | Intended for                            |
| ------ | ------- | --------------------------------------- |
| `id`   | green   | identifiers (commit hashes, ids, names) |
| `data` | cyan    | values / literals                       |
| `path` | dim     | filesystem paths                        |
| `cmd`  | blue    | commands to run                         |
| `misc` | dim     | secondary / detail text                 |
| `warn` | yellow  | warnings                                |
| `err`  | red     | errors                                  |

The `prop_*` helpers are just shortcuts for wrapping a value in its role, so
`.prop_id("commit", sha)` and `.prop("commit", "[id]{v}[/id]", v=sha)` are
equivalent. See [Customizing the theme](#customizing-the-theme) to override
colors or add roles.

### Escaping and the escape hatch

Because messages are markup templates, untrusted text (filenames, user input,
subprocess output) must never be interpolated raw, or a stray `[` could break
rendering or inject markup.

- **Safe by default.** Values passed as **template args** or through the
  **`prop_*` helpers** are escaped for you. Prefer these for anything untrusted:

  ```python
  CliError("cannot read [id]{commit}[/id]", commit=user_value)  # user_value escaped
  err.prop_path("file", path)                                   # path escaped
  ```

- **The escape hatch.** Inline f-string interpolation into a template is
  *deliberately not escaped* — it is the escape hatch for trusted, already-safe
  markup, and it is the caller's responsibility:

  ```python
  CliError(f"cannot read [id]{commit}[/id]")  # NOT escaped — only for trusted text
  ```

- **Manual escaping.** When you must build a string yourself, `escape()`
  (re-exported from `rich.markup.escape`) neutralizes markup in a value:

  ```python
  from cli_error import escape
  msg = f"saw {escape(untrusted)}"
  ```

Rule of thumb: reach for template args / `prop_*` for untrusted values; use
inline interpolation only for text you fully control.

## `CliExit` — signalling a clean exit

`CliExit(template, /, **args)` is not an error — it is a "nothing to do" signal.
When caught by the reporter's `handler()` it prints its message and exits with
status **0**. Use it for cases like `--version` or an empty work set:

```python
from cli_error import CliExit

if args.version:
    raise CliExit("myctl [data]{version}[/data]", version="1.2.3")

if not pending:
    raise CliExit("nothing to do")
```

## `CliReporter` — centralized output and exit handling

`CliReporter` is the single integration point for a CLI's output and exit
handling. Build a themed console, construct the reporter, and run your program
inside `reporter.handler()`. The handler translates exceptions into exit codes:

- `CliExit` → prints its message, exits `0`;
- any other `Exception` → renders it via `print_error`, exits `1` (plus a full
  traceback on stderr when `debug` is set);
- `KeyboardInterrupt` / `SystemExit` propagate untouched.

The example below is framework-agnostic (plain `argparse`) and wires a `--debug`
flag straight into the reporter:

```python
import argparse
import sys

from cli_error import CliError, CliExit, CliReporter, make_console


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="myctl")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("commit")
    return parser.parse_args(argv)


def run(reporter, args):
    reporter.debug_print("[misc]resolving {commit}[/misc]", commit=args.commit)
    if not args.commit:
        raise CliExit("nothing to do")
    raise CliError("cannot check out [id]{commit}[/id]", commit=args.commit)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    reporter = CliReporter(make_console(), debug=args.debug)
    with reporter.handler():        # raises SystemExit — let it propagate
        run(reporter, args)


if __name__ == "__main__":
    main()
```

`CliReporter(console, *, debug=False, show_locals=False, console_err=None)` — when
`console_err` is omitted a stderr console is built for you, inheriting the passed
console's `no_color` and theme so debug output matches your main console. Wire
`--debug` at construction as above; the flag is also a plain public attribute you
can toggle later (`reporter.debug = True`). `show_locals` sets the default for
`debug_traceback` (see below).

### Cause chains

When you re-raise with `raise … from err`, the reporter renders the underlying
cause as an indented `caused by:` line beneath the error:

```python
try:
    subprocess.run(["git", "checkout", commit], check=True)
except OSError as os_err:
    raise CliError("cannot check out [id]{commit}[/id]", commit=commit) from os_err
```

```
Error: cannot check out abc123
  caused by: [Errno 2] No such file or directory: 'git'
```

The chain is walked through `__cause__`/`__context__`, deduped so cycles stop.
`raise … from None` suppresses the context, hiding the `caused by:` line.

## Debug helpers

Every `debug_*` method is a **silent no-op unless the reporter's `debug` flag is
set**, and everything they emit is routed to the reporter's own **stderr**
console — never stdout, so debug output can't pollute machine-readable results.
Because they self-gate, you can sprinkle them freely without guarding each call.

| Method                         | Emits (only when `debug`)                          |
| ------------------------------ | -------------------------------------------------- |
| `debug_print(template, **args)`| a trusted template with escaped args               |
| `debug_traceback(show_locals=None)` | the currently-handled exception traceback     |
| `debug_cmd(cmd, cwd=None)`     | a subprocess command line and optional working dir |
| `debug_output(stdout, stderr)` | captured subprocess output (empty streams skipped) |

`debug_cmd` and `debug_output` unify the common pattern of tracing an external
command and its result:

```python
cmd = ["git", "checkout", commit]
reporter.debug_cmd(cmd, cwd=repo_path)

result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
reporter.debug_output(result.stdout, result.stderr)
```

`debug_traceback()` is what `handler()` calls for you on an uncaught exception,
so a `--debug` run automatically shows the full traceback on stderr alongside
the rendered error. Pass `show_locals=True` (per call, or as the
`CliReporter(show_locals=True)` default) to include each frame's local variables
— useful when debugging, but keep it developer-only since locals can expose
secrets like tokens or passwords.

## Customizing the theme

`make_console()` returns a Rich console pre-loaded with the default style roles.
To override colors or add your own roles, pass `styles`:

```python
from rich.style import Style
from cli_error import make_console

console = make_console(styles={"id": "bold magenta", "note": Style(italic=True)})
```

`make_console(*, styles=None, no_color=False, stderr=False)` — `no_color`
renders markup as plain text (no ANSI escapes), and `stderr` routes output to
`sys.stderr`. `make_theme(*, styles=None)` returns just the merged `Theme` if you
manage your own console. `DEFAULT_STYLES` exposes the built-in role → color map.

## Learn more

- [`CONTEXT.md`](CONTEXT.md) — project glossary (CliError, prop, hint, detail
  block, CliExit, CliReporter, debug diagnostic, theme, style role).
- [`docs/adr/0001-error-formatting-and-theming.md`](docs/adr/0001-error-formatting-and-theming.md)
  — the rationale behind error formatting and optional Rich theming.
- [`docs/adr/0002-cli-reporter-output-facade.md`](docs/adr/0002-cli-reporter-output-facade.md)
  — why output and error handling are unified behind the `CliReporter` façade.

## Testing

The repository is checked with `tox` (typecheck, test, lint):

```bash
uv run tox
```

## Release Notes

### v0.1.1
- `debug_traceback` can now render per-frame locals — opt in with `CliReporter(show_locals=True)` or a per-call `debug_traceback(show_locals=True)` override (locals may expose secrets, so keep it developer-only).
- The auto-built stderr console now inherits the injected console's `no_color` and theme intent, so debug output matches your main console's styling.

### v0.1.0
- `CliError` — structured exceptions with Rich-markup messages and a fluent builder for hints, detail blocks, and labelled context properties.
- `CliReporter` — output/exit façade: a context manager that maps exceptions to exit codes, renders the `caused by:` cause chain, and gates debug diagnostics behind a `debug` flag.
- `CliExit` — a clean-exit signal that prints its message and exits with status 0.
- Theming via `make_console`, `make_theme`, and `DEFAULT_STYLES` — Rich consoles with default style roles, per-role overrides, `no_color` degradation, and stderr routing.
- Automatic escaping of untrusted template/property values, plus standalone `render_error`, `render_template`, and `print_error` helpers.
