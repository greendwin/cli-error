---
id: s01t02
slug: support-python-3-10
status: pending
---

# Support Python 3.10

## Context

`cli-error` currently declares `requires-python = ">=3.12"`, but a consumer needs to install it on Python 3.10. Widen the supported range to `>=3.10` (which also covers 3.11) by fixing the two version-sensitive constructs in the source, lowering the packaging/tooling floor, and expanding CI + sandbox to prove the full 3.10–3.14 range. A supported-version claim is only valid once CI passes on that version, so proving the matrix green is part of the definition of done.

## Decisions

- **Floor is a hard, CI-enforced contract** — a real consumer needs 3.10; 3.10 and 3.11 join the CI matrix and a break on either is a release blocker. *Rejected: best-effort lower bound without CI proof — an unproven version claim is worthless.*
- **`Self` via version-guarded import + conditional dependency** — `if sys.version_info >= (3, 11): from typing import Self` else `from typing_extensions import Self`, plus `typing_extensions; python_version < "3.11"` as a conditional dependency. *Rejected: always importing from typing_extensions (adds an unconditional runtime dep for 3.11+ users); dropping `Self` for a TypeVar/class-name (loses the clean self-return typing on the 8 builder methods).*
- **`Generator[None]` → `Generator[None, None, None]`** — the three-arg form is valid on every version 3.10→3.14; smallest diff, no import change. Single-arg only became legal on 3.13 (PEP-696 defaults). *Rejected: switching to `Iterator[None]` — larger conceptual change than needed.*
- **Lower every tooling floor, including mypy's** — `requires-python = ">=3.10"`, black `target-version = ["py310", "py311", "py312"]`, and `[tool.mypy] python_version = "3.10"`. Pinning mypy to the floor is what turns "fixed the two we know about" into "the tools catch the next one" — analyzing as 3.12 is exactly what let `Generator[None]` slip through.
- **CI matrix expands to the full range** — `["3.10", "3.11", "3.12", "3.13", "3.14"]`.
- **Sandbox mirrors the full CI matrix** — `PYTHON_VERSION="3.10 3.11 3.12 3.13 3.14"` so the container reproduces both floor and ceiling; a version gap is where "green locally, red in CI" bugs hide.
- **Verify on a real 3.10 interpreter** — the `sys.version_info` branch and conditional `typing_extensions` dep only exercise on 3.10; confirm in the sandbox, not just on the 3.12 host.

## Edge cases

- **mypy resolving the else branch on the 3.12 dev host** — `from typing_extensions import Self` must type-check even though `typing_extensions` isn't installed in the 3.12 dev env; mypy resolves it from bundled typeshed, so this is fine, but confirm `uv run tox` stays green.
- **Runtime `typing_extensions` only on <3.11** — on 3.10 the conditional dep must actually be pulled in (via `uv run --python 3.10` / sandbox resolution) so the else-branch import doesn't `ImportError`.
- **No `from __future__ import annotations`** — `str | Style`, `Path | None` and `list[str]` are evaluated at definition time but all work at runtime on 3.10+ (PEP 604 / PEP 585); no shim needed, do not add the future import.
- **mypy `python_version = "3.10"` may surface new errors** — pinning the floor can flag other 3.11+-only assumptions; per CLAUDE.md, fix all reported tox issues including pre-existing.

## Key files

- `src/cli_error/_errors.py` — version-guarded `Self` import (line 1).
- `src/cli_error/_reporter.py` — `Generator[None]` → `Generator[None, None, None]` (line 93).
- `pyproject.toml` — `requires-python`, conditional `typing_extensions` dep, black `target-version`, `[tool.mypy] python_version`.
- `.github/workflows/ci.yml` — matrix `python-version` (line 20).
- `.sandbox/.env`, `.sandbox/.env.example`, `.sandbox/variants/python/Dockerfile` — `PYTHON_VERSION`.

## Acceptance criteria

- `import cli_error` and all its public builder methods (`hint`, `detail`, `prop*`) type-check and run on Python 3.10.
- `CliReporter.handler()` works as a context manager on 3.10 (the `Generator` annotation no longer errors).
- `uv run tox` (typecheck, test, lint) is green on the 3.12 host with `mypy python_version = "3.10"` in effect.
- The full test suite passes when run against a real 3.10 interpreter in the sandbox.
- CI runs and passes on all of 3.10, 3.11, 3.12, 3.13, 3.14.
- `pyproject.toml` declares `requires-python = ">=3.10"` and pulls `typing_extensions` only on <3.11.

## Open questions

- None.

## Out of scope

- **Version bump / release** — land the compatibility fixes only; the release is batched separately (user deferred).
- **CONTEXT.md** — no new glossary terms; this is purely an implementation change.
- **ADR** — lowering a support floor isn't a hard-to-reverse, surprising trade-off.
- **Classifiers / README version claims** — none currently exist advertising a floor, so nothing to update.
