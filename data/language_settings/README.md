# Language Settings

This directory contains per-language configuration files for the ipa-parser
library. Each file defines the custom character sequences and geminate handling
rules needed to correctly parse IPA transcriptions for a specific language.

## Directory Contents

| File | Format | Status |
|---|---|---|
| `Northwest_Sahaptin.toml` | TOML | Active (preferred) |
| `Italian.toml` | TOML | Active (preferred) |
| `Northern_Tepehuan.toml` | TOML | Active (preferred) |

TOML is the preferred format. Legacy Python snippet files contain bare
`CustomCharacter.add_char(...)` calls and must be executed directly; they are
being migrated to TOML.

---

## TOML Configuration Format

A TOML config file has one optional top-level key (`geminate`) and any number
of `[[custom_chars]]` array-of-tables blocks.

### Annotated example

```toml
# geminate (boolean, optional, default: true)
# When true, consecutive identical consonants are collapsed to a single segment
# before length is computed. Set to false for languages where geminates are
# phonologically contrastive.
geminate = false

# Each [[custom_chars]] block registers one multi-character sequence with the
# CustomCharacter registry. These sequences take priority over single-character
# IPA lookups during maximal munch segmentation.

[[custom_chars]]
sequence = "t͡s"       # The exact Unicode string to match (tie bar included)
category = "CONSONANT" # Phonological category (see table below)
rank = 1               # Phonological weight: 1 = counted, 0 = not counted

[[custom_chars]]
sequence = "t͡ʃ"
category = "CONSONANT"
rank = 1

[[custom_chars]]
sequence = "ai"
category = "VOWEL"     # Diphthong treated as a single vowel segment
rank = 1

[[custom_chars]]
sequence = "OP"
category = "PAUSE"     # Other-pause marker; excluded from phoneme counts
rank = 0

[[custom_chars]]
sequence = "SP"
category = "PAUSE"     # Sentence-pause marker; excluded from phoneme counts
rank = 0
```

---

## Field Reference

### `geminate`

| Type | Default | Required |
|---|---|---|
| boolean | `true` | No |

Controls geminate consonant collapsing in `IPAString`. When `true`,
repeated identical consonants (e.g., `pp`) are reduced to a single segment
before any metric is computed. Set to `false` when the language uses contrastive
gemination.

### `[[custom_chars]]` entries

Each block in the `[[custom_chars]]` array defines one custom sequence.

#### `sequence`

| Type | Required |
|---|---|
| string | Yes |

The exact Unicode string that should be treated as a single segment. Must be
non-empty. Tie bars (`͡`), apostrophes, length marks, and any other diacritics
are part of the sequence and must be included verbatim.

#### `category`

| Type | Required |
|---|---|
| string | Yes |

The phonological category assigned to this sequence. Valid values:

| Value | Description | Default rank |
|---|---|---|
| `CONSONANT` | Consonant phoneme | 1 |
| `VOWEL` | Vowel phoneme or diphthong | 1 |
| `DIPHTHONG` | Diphthong (treated as single segment) | 1 |
| `AFFRICATE` | Affricate consonant cluster | 1 |
| `PAUSE` | Pause marker (`OP`, `SP`, etc.) | 0 |

The category affects how `IPAString.segment_type` reports the segment and
how `IPAString.coda` classifies the final syllable.

`AFFRICATE` is normalized to `CONSONANT`, and `DIPHTHONG` is normalized to
`VOWEL` for C/V counts and segment-type mappings.

#### `rank`

| Type | Default | Required |
|---|---|---|
| integer | `1` | No |

Phonological weight used by `IPAString.total_length()`. Use `1` for segments
that contribute to phonological length (consonants, vowels, diphthongs,
affricates) and `0` for non-phonemic markers (pauses, boundary symbols).

---

## How Maximal Munch Uses Custom Characters

During segmentation, `IPAString._maximal_munch` scans the input string
left-to-right. At each position it checks every registered `CustomCharacter`
sequence and selects the longest match. Only if no custom sequence matches does
it fall back to a single-codepoint IPA lookup.

This means longer sequences always win. If you register both `"t͡s"` and `"t"`,
the parser will match `"t͡s"` wherever it appears.

---

## Loading a Config

### Via CLI

Pass `--config` with the path to your TOML file:

```bash
ipa-parser input.xlsx --config data/language_settings/Northwest_Sahaptin.toml
```

The CLI loads the config, applies custom characters via
`configure_custom_characters`, and uses the `geminate` value unless overridden
with `--geminate` / `--no-geminate`.

### Via Python

```python
from ipa import load_language_config
from ipa.pipeline import configure_custom_characters

geminate, custom_chars = load_language_config("data/language_settings/Northwest_Sahaptin.toml")
configure_custom_characters(custom_chars)
```

`load_language_config` returns:

- `geminate` — `bool`
- `custom_chars` — `list[tuple[str, str, int]]`, where each tuple is
  `(sequence, category, rank)`

`configure_custom_characters` clears the current `CustomCharacter` registry
and registers each entry from the list.

---

## Adding Custom Characters via the Interactive CLI

When using the interactive `ipa-parser` command, select option `7` to add a
custom character at runtime. The CLI prompts for:

1. `Sequence` — the Unicode string
2. `Category` — e.g., `CONSONANT`, `VOWEL`, `PAUSE`
3. `Rank` — integer weight (default `1`)

If a `--config` path was provided when the CLI was launched, the new entry is
appended to the TOML file automatically using `append_custom_char` from
`src/ipa/config.py`. If no config path was provided, the change is session-only
and is lost when the CLI exits.

---

## ipa_symbols.json Schema

The library's base IPA symbol definitions live in
`src/ipa/data/ipa_symbols.json`. Custom characters defined in TOML configs
extend (but do not replace) this base set.

### Top-level structure

```json
{
  "consonants": { ... },
  "vowels": { ... },
  "diacritics": { ... },
  "suprasegmentals": { ... },
  "tones": { ... },
  "accent_marks": { ... }
}
```

| Key | Internal category | Phonological weight |
|---|---|---|
| `consonants` | `CONSONANT` | 1 |
| `vowels` | `VOWEL` | 1 |
| `diacritics` | `DIACRITIC` | 0 |
| `suprasegmentals` | `SUPRASEGMENTAL` | 0 |
| `tones` | `TONE` | 0 |
| `accent_marks` | `ACCENT_MARK` | 0 |

### Symbol entry format

Each symbol entry object contains:

```json
{
  "symbol": "p",
  "name": "voiceless bilabial plosive",
  "alternates": []
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | Yes | The canonical Unicode IPA character(s) |
| `name` | string | Yes | Human-readable lowercase name |
| `alternates` | array of strings | Yes (may be empty) | Alternate Unicode representations for the same sound |

The JSON file stores `name` values in lowercase; `IPA_CHAR.name()` returns the
uppercased form at runtime.

Alternate representations are stored under derived names (e.g.,
`"VOICED VELAR PLOSIVE ALT g"`) and resolve to the same category and weight
as the canonical entry.

### How DictionaryLoader processes the file

1. Reads and JSON-parses the file.
2. Detects the official schema by checking for the presence of any known
   top-level category key.
3. Maps each JSON key to its internal category name
   (e.g., `"consonants"` -> `"CONSONANT"`).
4. Walks every symbol entry recursively, computing a lookup key by
   concatenating `format(ord(c), '04x')` for each codepoint in the symbol
   string (e.g., `"p"` -> `"0070"`).
5. Stores each entry as `{ "IPA": symbol, "code": hex_key }` under the
   uppercase name in the normalized map.
6. Builds a weight map (`CONSONANT: 1`, `VOWEL: 1`, all others: `0`).

The resulting data and weight maps are cached as class-level attributes on
`DictionaryLoader` and shared by `IPA_CHAR`.
