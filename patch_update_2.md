# Patch Update 2: Over-Engineering Fixes and AFFRICATE/DIPHTHONG Mapping

Date: 2026-02-23
Status: Completed (item 1 skipped)

This document captures findings from a full over-engineering sweep
(declutter, reviewer, documenter agents) and a planned bug fix for
AFFRICATE/DIPHTHONG category mapping. No changes have been applied yet.

---

## Phase 1: Quick Wins (Low Risk)

| # | Fix | File | Status |
|---|---|---|---|
| 1 | Remove CLI ASCII art banner | `src/ipa/cli.py` | Skipped |
| 2 | Remove narrating inline comments in `coda` and `stress()` | `src/ipa/ipa_string.py` | Completed |
| 3 | Simplify `collapse_nested_list` to a one-liner | `src/ipa/pipeline.py` | Completed |
| 4 | Remove unnecessary `cast()` calls | `src/ipa/pipeline.py` | Completed |

---

## Phase 2: ValidationError Simplification (Low Risk)

| # | Fix | File | Status |
|---|---|---|---|
| 5 | Replace ASCII-bordered error messages with clean f-string format | `src/ipa/debug.py` | Completed |

Current format:
```
--------------------------------------------------
                 ERROR OCCURRED
--------------------------------------------------
Symbol not found:
    'Q'
--------------------------------------------------
               END OF ERROR MESSAGE
--------------------------------------------------
```

Proposed format:
```
ValidationError [SYMBOL_NOT_FOUND]: Symbol not found: 'Q'
```

---

## Phase 3: Docstring Trimming (Low Risk)

| # | Fix | File | Lines | Status |
|---|---|---|---|---|
| 6 | Trim module docstring from 39 -> ~5 lines; point to README | `src/ipa/cli.py` | 1-39 | Completed |
| 7 | Trim module docstring (remove schema block), class docstring (dedup), `_category_weights` docstring to one-liner | `src/ipa/dict_loader.py` | 1-39, 45-61, 217-237 | Completed |
| 8 | Trim `coda` docstring (15 -> ~6 lines), `stress()` docstring (12 -> 1 line), remove `__init__` docstring (class docstring covers it) | `src/ipa/ipa_string.py` | 152-166, 200-218, 57-78 | Completed |
| 9 | Trim `clear_all_chars` and `is_valid_char` to one-liners | `src/ipa/ipa_char.py` | 260-267, 270-280 | Completed |
| 10 | Trim `configure_custom_characters` (18 -> ~4 lines), `scripts/ipa_parser.py` module docstring (14 -> 2 lines) | `src/ipa/pipeline.py`, `scripts/ipa_parser.py` | 1270-1292, 1-15 | Completed |

---

## Phase 4: Documentation Deduplication (Low Risk)

| # | Fix | File | Status |
|---|---|---|---|
| 11 | Collapse Code Style section to cross-reference CONTRIBUTING.md | `AGENTS.md` | Completed |
| 12 | Collapse Architecture section to one-line pointer to README | `AGENTS.md` | Completed |
| 13 | Replace Language Configuration section with summary + link to `data/language_settings/README.md` | `README.md` | Completed |
| 14 | Remove duplicate valid-category table, link to `data/language_settings/README.md` | `CONTRIBUTING.md` | Completed |

Current redundancy map:

Topic: Architecture Layers
  README.md  - Mermaid diagram + full table (authoritative)
  AGENTS.md  - Prose bullets (duplicate)

Topic: Code Style Rules
  CONTRIBUTING.md  - Full section with sub-headings (authoritative)
  AGENTS.md        - Identical rules as terse bullets (duplicate)

Topic: TOML Config Format
  data/language_settings/README.md  - Full reference (authoritative)
  README.md                         - Example block + load snippet (duplicate)
  CONTRIBUTING.md                   - Example block + category table (duplicate)

After dedup: each topic lives in one authoritative file; others cross-reference.

---

## Phase 5: AFFRICATE/DIPHTHONG Mapping (Bug Fix)

### Problem

`segment_count`, `coda`, pipeline `segment_type()`, and ISI counts only
recognize exact 'CONSONANT' and 'VOWEL' categories. Custom characters
registered as 'AFFRICATE' or 'DIPHTHONG' are silently excluded from all
C/V tallies.

Affricates are phonologically consonants. Diphthongs are phonologically
vowels. The mapping should be transitive.

### Affected Code Paths

| File | Line | Issue |
|---|---|---|
| `src/ipa/ipa_string.py` | 98-106 | `segment_type` returns 'AFFRICATE'/'DIPHTHONG' as-is |
| `src/ipa/ipa_string.py` | 120 | `segment_count` only counts 'VOWEL' and 'CONSONANT' |
| `src/ipa/ipa_string.py` | 191 | `coda` only checks `phone_type == 'CONSONANT'` |
| `src/ipa/pipeline.py` | 422-424 | `segment_type()` maps only CONSONANT->C, VOWEL->V |
| `src/ipa/interactive.py` | 288-290 | Same unmapped C/V pattern |
| `src/ipa/pipeline.py` | 954-962 | ISI counts derived from C/V column (cascading) |

### Fix Strategy (Single Point of Truth)

Normalize in `IPAString.segment_type` property:
- 'AFFRICATE' -> 'CONSONANT'
- 'DIPHTHONG' -> 'VOWEL'

This automatically fixes `segment_count`, pipeline `segment_type()`,
interactive `_inspect_word()`, and all ISI counts.

The `coda` property bypasses `segment_type` (reads categories directly),
so it needs a separate fix: `if phone_type in ('CONSONANT', 'AFFRICATE'):`.

`AFFRICATE` and `DIPHTHONG` remain valid category strings in TOML configs
and CustomCharacter registry. They are normalized only at query time.

`ranking_dictionary` already assigns weight 1 to both - no change needed.

### Fixes

| # | Fix | File | Status |
|---|---|---|---|
| 15 | Add AFFRICATE->CONSONANT, DIPHTHONG->VOWEL mapping in `segment_type` property | `src/ipa/ipa_string.py` | Completed |
| 16 | Add AFFRICATE check alongside CONSONANT in `coda` property | `src/ipa/ipa_string.py` | Completed |
| 17 | Update `segment_count` docstring (remove "not counted" note) | `src/ipa/ipa_string.py` | Completed |
| 18 | Update language_settings/README.md to document the mapping | `data/language_settings/README.md` | Completed |
| 19 | Add tests: AFFRICATE in segment_count (C), DIPHTHONG in segment_count (V), AFFRICATE in coda | `tests/test_ipa_string.py` | Completed |

---

## Phase 6: Pipeline DRY (Medium Risk)

| # | Fix | File | Status |
|---|---|---|---|
| 20 | Extract repeated OP/SP pass-through pattern into `_apply_to_words()` helper | `src/ipa/pipeline.py` | Completed |

Five pipeline functions repeat the same pattern:
```
if word == "OP" or word == "SP":
    result.append(word)
else:
    result.append(IPAString(word, geminate=geminate).some_property)
```

Functions: `coda_column`, `stress_column`, `syllable_length_by_phoneme`,
`word_length_by_phoneme`, `word_length_by_syllable`.

---

## Phase 7: TODO.md Updates

### Add to Completed (after execution):
- Over-engineering fixes (Phases 1-4, 6)
- AFFRICATE/DIPHTHONG transitive category mapping

### Add to Medium Priority (Deferred):
- Refactor `IPA_CHAR`/`CustomCharacter`/`DictionaryLoader` from classmethod-only
  classes to module-level functions (API-breaking; defer to major version)
- Simplify interactive CLI menu with dispatch dict

---

## Phase 8: Verification

- `pytest` - all tests pass
- `ruff check src tests scripts` - clean
- `mypy src tests` - no new issues
- Pipeline run: `ipa-parser data/unprocessed/NorthwestSahaptin.xlsx --config data/language_settings/Northwest_Sahaptin.toml --run`

---

## Deferred Items (Not in This Patch)

| Item | Reason |
|---|---|
| Refactor IPA_CHAR/CustomCharacter/DictionaryLoader to functions | Would break public API; defer to major version |
| Simplify interactive CLI with dispatch dict | Works fine; low priority |
| Remove AFFRICATE/DIPHTHONG from ranking_dictionary | Harmless safety net; keep for now |
