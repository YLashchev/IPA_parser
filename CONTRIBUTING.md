# Contributing to ipa-parser

Thank you for contributing to ipa-parser. This guide covers the development
workflow, code style expectations, and the procedures for extending the library
with new IPA symbols, language configurations, and custom characters.

## Table of Contents

- [Development Environment](#development-environment)
- [Running Tests](#running-tests)
- [Linting and Type Checking](#linting-and-type-checking)
- [Code Style Conventions](#code-style-conventions)
- [Adding New IPA Symbols](#adding-new-ipa-symbols)
- [Adding Language Configurations](#adding-language-configurations)
- [Adding Custom Characters](#adding-custom-characters)
- [Error Handling](#error-handling)
- [Pull Request Workflow](#pull-request-workflow)

---

## Development Environment

### 1. Clone the repository and create a virtual environment

```bash
git clone <repository-url>
cd IPA_parser
python -m venv .venv
```

### 2. Upgrade packaging tooling

```bash
.venv/bin/python -m pip install -U pip setuptools wheel
```

### 3. Install the package in editable mode with development dependencies

```bash
.venv/bin/python -m pip install -e ".[dev]"
```

This installs `pytest`, `pytest-cov`, `ruff`, and `mypy` in addition to the
runtime dependencies (`pandas`, `openpyxl`).

### 4. (Optional) Register a Jupyter kernel

```bash
.venv/bin/python -m ipykernel install --user --name ipa-parser
```

### Project layout

```
src/ipa/              Library source code
tests/                Unit tests
scripts/              Thin CLI wrapper script
notebooks/            Analysis workflow notebooks
data/unprocessed/     Input Excel sheets for analysis
data/processed/       Pipeline output (CSV/XLSX, gitignored)
data/language_settings/  Per-language TOML configs
pyproject.toml        Package metadata, tool config
requirements.txt      Pinned runtime dependencies
```

---

## Running Tests

Run the full test suite:

```bash
pytest
```

Run a single test:

```bash
pytest tests/test_ipa_string.py::test_basic_segments
```

Run with coverage:

```bash
pytest --cov=ipa --cov-report=term-missing
```

Tests use the `conftest.py` fixture `clear_custom_chars`, which resets
`CustomCharacter` state between tests automatically. Keep this fixture in place
and do not rely on global `CustomCharacter` state across test functions.

---

## Linting and Type Checking

Lint all source, test, and script files:

```bash
ruff check src tests scripts
```

Run incremental type checking:

```bash
mypy src tests
```

Mypy is configured with `strict = false`. Add annotations when you touch
existing code, but avoid large refactors solely for type coverage.

---

## Code Style Conventions

### Formatting

- Use 4-space indentation. Do not use tabs.
- Maximum line length is 100 characters (enforced by ruff).
- Use ASCII in code and comments unless IPA symbols are required in the text.

### Import order

1. Standard library imports
2. Third-party imports (`pandas`, `openpyxl`, etc.)
3. Local imports (`from .ipa_char import ...`)

Prefer explicit imports over wildcard imports.

### Naming

| Construct | Convention | Example |
|---|---|---|
| Classes | CamelCase | `IPAString`, `CustomCharacter` |
| Functions and methods | snake_case | `total_length`, `load_language_config` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_COLUMNS`, `FINAL_COLUMNS` |

### IPA and Unicode

- Do not normalize away diacritics or tie bars anywhere in library code.
- `src/ipa/data/ipa_symbols.json` is the only data source for IPA symbols.
  Do not introduce separate lookup tables or hardcoded symbol lists.
- Keep `ipa_symbols.json` and the parsing logic in sync whenever you add symbols.

### Pandas

- Keep numeric columns numeric during processing. Apply `fillna("N/A")` or
  `na_rep="N/A"` only at export time.
- Use `.copy()` when creating final DataFrame slices to avoid view assignment
  warnings.

---

## Adding New IPA Symbols

All IPA symbols are defined in `src/ipa/data/ipa_symbols.json`. This file is
the single source of truth for the library.

### File structure

The JSON has six top-level category keys. Each maps to a nested structure that
eventually contains symbol entry objects:

```
consonants
vowels
diacritics
suprasegmentals
tones
accent_marks
```

Each symbol entry must have the following fields:

```json
{
  "symbol": "<IPA character>",
  "name": "<human-readable name>",
  "alternates": []
}
```

- `symbol`: the canonical Unicode IPA character (or multi-character sequence).
- `name`: a lowercase descriptive name (e.g., `"voiceless bilabial plosive"`).
- `alternates`: an array of alternate Unicode representations for the same sound.
  May be empty. The loader registers each alternate under a derived name.

### Steps to add a symbol

1. Open `src/ipa/data/ipa_symbols.json`.
2. Locate the appropriate category and subcategory.
3. Add a new entry object with `symbol`, `name`, and `alternates`.
4. Run the tests to confirm the symbol is recognized:

```bash
pytest
```

5. Optionally verify the lookup directly:

```python
from ipa import IPA_CHAR
IPA_CHAR.category("<new symbol>")
```

### What DictionaryLoader does with the file

`DictionaryLoader` reads the JSON at import time and walks every symbol entry,
computing a hex-code key by concatenating `format(ord(c), '04x')` for each
codepoint in the symbol string. The resulting in-memory map is queried by
`IPA_CHAR` for every character lookup. Alternate representations are stored as
separate entries under derived names.

---

## Adding Language Configurations

Language-specific custom characters are stored in TOML files under
`data/language_settings/`. TOML is the preferred format. Legacy Python snippet
files in the same directory are being migrated to TOML.

### TOML format

```toml
# Collapse consecutive identical consonants (geminate reduction).
# Set to false if geminates are phonologically contrastive.
geminate = true

# Each [[custom_chars]] block defines one multi-character sequence.
[[custom_chars]]
sequence = "t͡s"    # The exact Unicode string to match during segmentation
category = "CONSONANT"
rank = 1            # Phonological weight: 1 for consonants/vowels, 0 for pauses/marks

[[custom_chars]]
sequence = "OP"
category = "PAUSE"
rank = 0
```

For valid category values and rank semantics, see
[`data/language_settings/README.md`](../data/language_settings/README.md).

### Loading a config

Via CLI:

```bash
ipa-parser data/unprocessed/input.xlsx --config data/language_settings/my_language.toml
```

Via Python:

```python
from ipa import load_language_config
from ipa.pipeline import configure_custom_characters

geminate, custom_chars = load_language_config("data/language_settings/my_language.toml")
configure_custom_characters(custom_chars)
```

`load_language_config` returns `(geminate: bool, custom_chars: list[tuple[str, str, int]])`.

See [`data/language_settings/README.md`](data/language_settings/README.md) for
the full format reference.

### Saving and updating configs (Python API)

Use these helpers when you want to persist changes programmatically:

```python
from ipa import save_language_config, append_custom_char

save_language_config(
    "data/language_settings/my_language.toml",
    geminate=True,
    custom_chars=[("t͡s", "CONSONANT", 1)],
)

append_custom_char(
    "data/language_settings/my_language.toml",
    "OP",
    "PAUSE",
    0,
)
```

`save_language_config` overwrites the TOML file, while `append_custom_char`
updates or appends a single entry. Both require the parent directory to exist.

---

## Adding Custom Characters

Custom characters extend the base IPA symbol set with multi-character sequences
such as affricates, diphthongs, and language-specific clusters. They take
priority during maximal munch segmentation.

### At runtime (Python API)

```python
from ipa import CustomCharacter

# Add a tie-bar affricate
CustomCharacter.add_char("t͡s", "CONSONANT", rank=1)

# Add a diphthong
CustomCharacter.add_char("ai", "VOWEL", rank=1)

# Add a pause marker
CustomCharacter.add_char("OP", "PAUSE", rank=0)
```

### Via the interactive CLI

Select option `7` from the interactive menu. The CLI prompts for sequence,
category, and rank. If a `--config` path was provided, the new entry is
appended to the TOML file automatically.

### Via TOML (recommended for reproducibility)

Add a `[[custom_chars]]` block to the language TOML file. The config is loaded
at startup and applied before any parsing occurs.

---

## Error Handling

- Use `ValidationError` (from `ipa.debug`) for all validation failures in
  library code. Do not use bare `Exception` or `print` statements for errors.
- Validate inputs early — check for empty strings and unrecognized symbols
  before processing.
- `IPA_CHAR` raises `ValidationError("EMPTY_INPUT_CHARACTER")` for empty input
  and `ValidationError("SYMBOL_NOT_FOUND", char=...)` for unknown symbols.
- `IPAString` raises `ValidationError("INVALID_SEGMENT", segment=..., string=...)`
  when one or more segments cannot be resolved.
- `DictionaryLoader` raises `ValidationError("FILE_NOT_FOUND", ...)` or
  `ValidationError("INVALID_JSON", ...)` if the data file is missing or malformed.

Example:

```python
from ipa import ValidationError, IPAString

try:
    result = IPAString("p@a")
except ValidationError as exc:
    print(exc)   # Formatted error message printed to stdout
```

---

## Pull Request Workflow

1. Create a feature branch from `main`.
2. Make your changes, following the conventions in this guide.
3. Add or update tests in `tests/` to cover new behavior.
4. Ensure all checks pass:

```bash
pytest
ruff check src tests scripts
mypy src tests
```

5. Update `AGENTS.md` and `TODO.md` if workflows or the backlog have changed.
   If you generate a sweep report, add a new `patch_update_*_completed.md`
   file and leave archived reports unchanged.
6. Open a pull request with a clear description of what was changed and why.
