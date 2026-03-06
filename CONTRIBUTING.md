# Contributing to ipa-parser

This guide covers local setup, checks, and the project-specific rules that matter
when changing parsing behavior, symbols, or language configs.

## Setup

```bash
python -m venv .venv
.venv/bin/python -m pip install -U pip setuptools wheel
.venv/bin/python -m pip install -e ".[dev]"
```

Optional Jupyter kernel:

```bash
.venv/bin/python -m ipykernel install --user --name ipa-parser
```

## Project Layout

```text
src/ipa/                  library source
tests/                    unit tests
scripts/                  CLI wrapper scripts
notebooks/                analysis notebooks
data/unprocessed/         input Excel sheets
data/processed/           pipeline output
data/language_settings/   per-language TOML configs
```

## Checks

```bash
pytest
pytest --cov=ipa --cov-report=term-missing
ruff check src tests scripts
mypy src tests
```

Run a single test with:

```bash
pytest tests/test_ipa_string.py::test_basic_segments
```

## Project Rules

### Parsing and IPA data
- `src/ipa/data/ipa_symbols.json` is the single source of truth for IPA symbols
- Do not normalize away diacritics or tie bars in library code
- Keep symbol-table changes aligned with parsing behavior
- `IPAString` uses maximal munch segmentation; change it carefully

### Errors
- Use `ValidationError` for validation failures
- Validate bad input early instead of printing errors

### Dataframes
- Keep numeric columns numeric during processing
- Convert display placeholders like `N/A` only at export time
- Use `.copy()` when building final slices from existing frames

### Imports and style
- Use 4-space indentation
- Prefer explicit imports
- Order imports as stdlib, third-party, local
- Use ASCII unless IPA symbols are required

## Adding IPA Symbols

Edit `src/ipa/data/ipa_symbols.json` and add the symbol under the right top-level
category:

- `consonants`
- `vowels`
- `diacritics`
- `suprasegmentals`
- `tones`
- `accent_marks`

Each entry needs:

```json
{
  "symbol": "<IPA character>",
  "name": "<human-readable name>",
  "alternates": []
}
```

After changes, run `pytest` and verify the symbol is recognized.

## Adding Language Configs

Language configs live in `data/language_settings/*.toml`.

Example:

```toml
geminate = true

[[custom_chars]]
sequence = "t͡s"
category = "CONSONANT"
weight = 1
```

Load a config with:

```python
from ipa import load_language_config
from ipa.pipeline import configure_custom_characters

geminate, custom_chars = load_language_config("data/language_settings/my_language.toml")
configure_custom_characters(custom_chars)
```

See `data/language_settings/README.md` for the full format.

## Adding Custom Characters

Register runtime-only custom characters with `CustomCharacter`:

```python
from ipa import CustomCharacter

CustomCharacter.add_char("t͡s", "CONSONANT", p_weight=1)
CustomCharacter.add_char("OP", "PAUSE", p_weight=0)
```

For reproducible workflows, prefer storing them in a TOML config.

## Pull Request Checklist
- Add or update tests for changed behavior
- Run `pytest`, `ruff check src tests scripts`, and `mypy src tests`
- Update docs only where behavior or workflow actually changed
- Keep unrelated formatting churn out of the PR
