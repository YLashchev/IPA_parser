# IPA Parser

![Python >= 3.11](https://img.shields.io/badge/python-%3E%3D3.11-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

Unicode IPA parser and analysis toolkit for phonological workflows.

The library parses IPA strings phonetically rather than character-by-character.
It uses grapheme-cluster-aware maximal munch segmentation backed by
`src/ipa/data/ipa_symbols.json`.

## Install

```bash
python -m venv .venv
.venv/bin/python -m pip install -e .
```

For development:

```bash
.venv/bin/python -m pip install -e ".[dev]"
```

## CLI Usage

Start interactive mode:

```bash
ipa-parser
```

Run directly with explicit paths:

```bash
ipa-parser data/unprocessed/NorthwestSahaptin.xlsx \
  --config data/language_settings/Northwest_Sahaptin.toml --run
```

If `--config` is omitted, the CLI prompts for a language config. If no TOML
config exists, the parser falls back to `geminate=True` and default pause
markers.

### Main flags

| Flag | Description |
|---|---|
| `--config PATH` | Language config TOML |
| `--geminate` / `--no-geminate` | Override geminate handling |
| `--run` | Skip interactive menu and run immediately |
| `--format {csv,xlsx,both}` | Output format |
| `--output-csv PATH` | Override CSV path |
| `--output-xlsx PATH` | Override XLSX path |

## Library Quick Start

```python
from ipa import IPAString

word = IPAString("bə.ˈnæ.nə")

word.segments
# ['b', 'ə', '.', 'ˈ', 'n', 'æ', '.', 'n', 'ə']

word.total_length()
# 6

word.syllables
# ['bə', 'ˈnæ', 'nə']
```

Use `CustomCharacter` for multi-character sequences that should win during
segmentation:

```python
from ipa import CustomCharacter

CustomCharacter.add_char("t͡s", "AFFRICATE", p_weight=1)
CustomCharacter.add_char("ai", "DIPHTHONG", p_weight=1)
CustomCharacter.add_char("OP", "PAUSE", p_weight=0)
```

## Core Concepts
- `IPAString` tokenizes and analyzes an IPA string
- `IPA_CHAR` looks up category, name, code, and phonological weight
- `CustomCharacter` registers language-specific multi-character sequences
- `ValidationError` is the project's validation exception type

`IPAString` depends on maximal munch segmentation, so custom sequences and
symbol-table changes can affect parsing behavior.

## Language Configuration

Language-specific settings live in `data/language_settings/*.toml`.

Example:

```toml
geminate = true

[[custom_chars]]
sequence = "t͡s"
category = "CONSONANT"
weight = 1

[[custom_chars]]
sequence = "OP"
category = "PAUSE"
weight = 0
```

Load from Python:

```python
from ipa import load_language_config
from ipa.pipeline import configure_custom_characters

geminate, custom_chars = load_language_config(
    "data/language_settings/my_language.toml"
)
configure_custom_characters(custom_chars)
```

See `data/language_settings/README.md` for the full config reference.

## Data Model
- IPA symbols are defined in `src/ipa/data/ipa_symbols.json`
- Keep that file in sync with parsing logic
- Do not introduce separate symbol tables

## Development

```bash
.venv/bin/python -m pip install -e ".[dev]"
pytest
ruff check src tests scripts
mypy src tests
```

See `CONTRIBUTING.md` for contributor workflow and project-specific rules.

## License

MIT
