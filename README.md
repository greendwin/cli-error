# cli-error

Error handling and reporting utilities for CLI applications.

## Getting started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### Setup

```bash
uv sync
```

### Usage

```python
from cli_error import CliError, CliExit, escape, make_console

console = make_console()

try:
    raise CliError("cannot read [id]{commit}[/id]", commit="a[b]c")
except CliError as error:
    console.print(f"[err]Error:[/err] {error.message}")
```

### Testing

```bash
uv run tox
```
