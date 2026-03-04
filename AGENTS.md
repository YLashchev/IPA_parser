# AGENTS.md

This file guides agentic coding assistants working in this repository.
Follow existing conventions unless a change is explicitly requested.

## Project Overview
- Package name: ipa-parser
- Python package lives in `src/ipa`
- Primary user workflow: notebooks and scripts in `notebooks/` and `scripts/`
- Core logic: IPA parsing and phonological analysis
- Data assets: IPA symbol table in `src/ipa/data/ipa_symbols.json`

## Repository Layout
- `src/ipa/`: library code
- `tests/`: unit tests
- `scripts/`: runnable scripts (e.g., `scripts/ipa_parser.py`)
- `notebooks/`: analysis notebooks
- `data/`: input sheets and language settings
- `pyproject.toml`: package metadata and dependencies
- `requirements.txt`: pinned runtime dependencies for the venv

## Environment Setup
- Create venv: `python -m venv .venv`
- Upgrade pip tooling: `.venv/bin/python -m pip install -U pip setuptools wheel`
- Install deps: `.venv/bin/python -m pip install -r requirements.txt`
- Editable install (recommended): `.venv/bin/python -m pip install -e .`
- Dev install: `.venv/bin/python -m pip install -e .[dev]`

## Build / Package
- Build wheel/sdist (if needed): `python -m pip install build && python -m build`
- There is no custom build script beyond setuptools metadata.

## Run Commands
- Run the script: `.venv/bin/python scripts/ipa_parser.py`
- Notebook usage: open `notebooks/Ling199_Sheet_Automator.ipynb`

## Test Commands
- Run tests: `pytest`

## Single Test Command
- Run one test: `pytest tests/test_ipa_string.py::test_name`

## Lint / Format
- Lint: `ruff check src tests`
- Formatting: not configured (avoid reformatting noise).

## Types
- Types: `mypy src tests`

## Code Style Guidelines

### Imports
- Prefer explicit imports (avoid wildcard imports).
- Order imports as: stdlib, third-party, local (`src/ipa/...`).
- Keep one import per line when adding new ones.

### Formatting
- Use 4-space indentation.
- Keep line lengths reasonable (no strict formatter enforced).
- Avoid introducing non-ASCII characters unless required for IPA data.

### Naming
- Classes: `CamelCase` (e.g., `IPAString`, `CustomCharacter`).
- Functions/methods: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Use descriptive names for dataframes and lists.

### Types
- Type hints are minimal today; add only if it improves clarity.
- If adding hints, keep them consistent and lightweight.

### Error Handling
- Use `ValidationError` from `src/ipa/debug.py` for validation failures.
- Prefer raising exceptions over printing errors.
- Validate inputs early (empty strings, invalid symbols).

### Data Handling
- Preserve IPA and Unicode handling; do not normalize away diacritics.
- `CustomCharacter` is the extension mechanism for language-specific IPA.
- `IPAString` relies on maximal munch segmentation; avoid changing it lightly.
- Keep `ipa_symbols.json` in sync with parsing logic when modifying data.

### Pandas Usage
- Keep numeric columns numeric during processing.
- Convert to display strings (e.g., "N/A") only at final export.
- Use `.copy()` when creating `final_df` from slices to avoid view pitfalls.

### Side Effects
- Scripts and notebooks often mutate dataframes in place; be explicit.
- Avoid modifying global state in `src/ipa` unless required.

## Notebook Conventions
- The notebook assumes the package is installed editable from repo root.
- Prefer `.venv/bin/python -m pip install -e .` for local usage.
- Use absolute paths when exporting outputs to avoid confusion.

## Packaging Notes
- Package is installed from `src/` using setuptools `package-dir`.
- Keep `src/ipa/data/*.json` included via package data.

## OS/Path Expectations
- This repo runs on macOS and Linux.
- Avoid hardcoded absolute paths inside library code.
- Scripts may use explicit output paths when needed.

## Cursor/Copilot Rules
- No `.cursorrules`, `.cursor/rules/`, or `.github/copilot-instructions.md` found.
- If added later, update this file to reflect them.

## When Adding New Workflows
- If you add tests or linting, update this file with exact commands.
- If you add scripts, document expected inputs/outputs here.
