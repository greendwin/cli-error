---
id: s01t0109
slug: deployment-setup-ci-release-workflows
status: done
---

# Deployment setup (CI + release workflows)

## Goal

GitHub Actions run tests on every push/PR to `main` and publish `cli-error` to PyPI on release. `.github/workflows/ci.yml` runs `uv run tox` across a Python matrix; `.github/workflows/release.yml` builds and publishes via PyPI trusted publishing on a published GitHub release.

## Decisions & constraints

- **Mirror repo-skills' setup** — `actions/checkout@v4`, `astral-sh/setup-uv@v5` (with `enable-cache` + `cache-dependency-glob: uv.lock`), `uv python install`, `uv sync --group dev`, `uv run tox`; release uses `uv build` + `pypa/gh-action-pypi-publish@release/v1` with `id-token: write` (trusted publishing, no API token).
- **Trim the Python matrix to the project floor** — `cli-error` is `requires-python >=3.12`, so CI runs `["3.12", "3.13", "3.14"]` (not repo-skills' 3.10/3.11).
- CI triggers: `push` and `pull_request` to `main`. Release trigger: `release: [published]`, environment `Production`.

## Edge cases

- Ensure `tox.ini` env list is compatible with the 3.12–3.14 matrix (no py310/py311-only envs that would fail).
- Trusted publishing requires the PyPI project/publisher to be configured out-of-band — note this as a prerequisite in the task, not something the workflow can self-provision.
- Distribution name in `pyproject.toml` must be `cli-error` for the publish to target the right project.

## Key files

- `.github/workflows/ci.yml` — new.
- `.github/workflows/release.yml` — new.
- `tox.ini` / `pyproject.toml` — confirm Python-version alignment with the matrix.

## Acceptance criteria

- `ci.yml` runs `uv run tox` on push/PR to `main` across Python 3.12, 3.13, 3.14.
- `release.yml` builds and publishes to PyPI on `release: published` via trusted publishing (`id-token: write`, no token secret).
- Workflows are valid YAML and reference `cli-error`.
- `uv run tox` remains green locally.
