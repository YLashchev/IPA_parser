# AGENTS.md

Guidance for coding agents working in this repository.

## Project Overview
- Package: `ipa-parser`
- Source: `src/ipa`
- Main workflows: notebooks in `notebooks/` and scripts in `scripts/`
- Core domain: IPA parsing and phonological analysis
- Symbol data: `src/ipa/data/ipa_symbols.json`

## Repository Layout
- `src/ipa/` - library code
- `tests/` - unit tests
- `scripts/` - runnable scripts
- `notebooks/` - analysis notebooks
- `data/` - input sheets and language settings
- `qmd-knowledge/` - project memory notes

## Setup And Commands
- Create venv: `python -m venv .venv`
- Install runtime deps: `.venv/bin/python -m pip install -r requirements.txt`
- Install editable: `.venv/bin/python -m pip install -e .`
- Install dev deps: `.venv/bin/python -m pip install -e .[dev]`
- Run CLI script: `.venv/bin/python scripts/ipa_parser.py`
- Run tests: `pytest`
- Run one test: `pytest tests/test_ipa_string.py::test_basic_segments`
- Lint: `ruff check src tests`
- Type check: `mypy src tests`

## QMD Memory
Before answering repo-specific questions about conventions, past fixes, debugging
history, design choices, or "why", search QMD first.

- Collection: `IPA_parser`
- Preferred tools: `vector_search` for semantic search, `search` for exact terms
- If QMD has relevant results, use them
- If not, proceed normally and say no relevant QMD memory was found when it matters

Use `qmd_memory` when available for search, dedupe, and recording.

### Learning vs issue
- `learning`: reusable convention, pattern, architecture lesson, or debugging takeaway
- `issue`: concrete bug, limitation, failure mode, workaround, regression, or fix history

Prefer `issue` when a specific problem was diagnosed, reproduced, worked around,
or fixed.

Before creating a new note, search for similar notes and update an existing one
when that is a better fit.

### QMD constraints
- Knowledge base must live in `qmd-knowledge/`, not a dot-directory
- `deep_search` is disabled in OpenCode on this machine for memory-safety reasons
- Use `./scripts/qmd-start.sh` if QMD needs to be started or warmed
- If the collection looks stale, follow `QMD_WORKFLOW.md`

## Code Style

### Imports
- Prefer explicit imports
- Order imports as stdlib, third-party, local

### Naming
- Classes: `CamelCase`
- Functions and methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Formatting
- Use 4-space indentation
- Keep lines reasonable
- Avoid non-ASCII unless IPA data requires it

### Error handling
- Use `ValidationError` from `src/ipa/debug.py` for validation failures
- Prefer raising exceptions over printing errors
- Validate empty strings and invalid symbols early

### Data handling
- Preserve IPA and Unicode behavior; do not normalize away diacritics
- `CustomCharacter` is the extension mechanism for language-specific IPA
- `IPAString` depends on maximal munch segmentation; change carefully
- Keep `ipa_symbols.json` aligned with parsing logic

### Pandas
- Keep numeric columns numeric during processing
- Convert placeholders like `N/A` only at final export
- Use `.copy()` when building final slices

### Paths and packaging
- Avoid hardcoded absolute paths in library code
- Package data under `src/ipa/data/*.json` must remain included

## Notebook And Script Conventions
- The notebook expects an editable install from repo root
- Scripts and notebooks may mutate dataframes in place; be explicit
- Absolute output paths are fine in scripts when needed

## Session Wrap-Up
At the end of a meaningful session, run `/wrap-up` to review work and record
durable learnings or issues to QMD.

## Maintenance
- If workflows change, update this file with the exact commands or rules that matter
- If tests, lint, or scripts change, keep the command list current
