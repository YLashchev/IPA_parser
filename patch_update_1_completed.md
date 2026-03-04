# Directory Update

Date: 2026-02-23

Status: Completed (archived). This report is historical and should not be modified further.

This file captures the declutter, documentation, and code review sweeps. Each section is authored by the corresponding agent.

## Declutter Sweep

Status: Ready

The repository is clean. All build artifacts and cache directories are already properly gitignored.

**Artifacts to remove:** None. All cached/generated artifacts are already gitignored:
- `.ruff_cache/` (gitignored)
- `.pytest_cache/` (gitignored)
- `__pycache__/` directories (gitignored)
- `*.egg-info/` directories (gitignoreed)
- `.venv/` (gitignored)
- `data/processed/*.csv` and `data/processed/*.xlsx` (gitignored)
- `**/.DS_Store` (gitignored)

**Gitignore gaps:** None. The `.gitignore` is comprehensive for this Python project.

**Ambiguous items needing user input:**
- `data/language_settings/Italian` - Legacy plain text config (not .toml format). May want to convert to TOML per AGENTS.md conventions.
- `data/language_settings/Northern_Tepehuan` - Legacy plain text config (not .toml format). May want to convert to TOML per AGENTS.md conventions.

These legacy config files are still functional but do not follow the TOML preference stated in AGENTS.md.

## Documenter Sweep

Status: Needs updates

### Stale Docs / Missing References

- **`data/language_settings/README.md` — stale directory table**: The "Directory Contents" table lists five legacy Python snippet files (`Italian`, `Northern_Sahaptin`, `Northern_Tepehuan`, `Northwest_Sahaptin`, `ZwaraBerber`). Only two of those files actually exist on disk (`Italian`, `Northern_Tepehuan`). `Northern_Sahaptin`, `Northwest_Sahaptin` (legacy), and `ZwaraBerber` are listed but absent. The table should be pruned to match real directory contents.
- **`README.md` — `segment_type` example output is misaligned with `segments` example**: The "Segments and Types" example shows `result.segments` as an 8-element list but the `segment_type` list immediately below has 9 elements. The `segments` list is also missing the leading stress mark `ˈ` implied by the input word `"bə.ˈnæ.nə"`. Both example outputs need to be re-derived from the actual input word.
- **`README.md` — `IPA_CHAR.name()` example shows wrong case**: The example shows `IPA_CHAR.name("p")  # "voiceless bilabial plosive"` (lowercase), but `DictionaryLoader._store_symbol` normalizes all names to uppercase via `str(name).upper()`, so the actual return value is `"VOICELESS BILABIAL PLOSIVE"`. The example should reflect the real return value.
- **`CONTRIBUTING.md` — `save_language_config` and `append_custom_char` undocumented**: Both functions are defined in `src/ipa/config.py` and used by the interactive CLI, but neither appears anywhere in `CONTRIBUTING.md`. Readers who want to extend or persist configurations programmatically have no guidance here.
- **`CONTRIBUTING.md` — PR workflow does not mention `patch_update_1_completed.md`**: Step 5 of the Pull Request Workflow tells contributors to update `AGENTS.md` and `TODO.md`, but the new sweep log file `patch_update_1_completed.md` is not mentioned.
- **`AGENTS.md` — notebook import path may be stale**: The notebook `notebooks/Ling199_Sheet_Automator.ipynb` is referenced, and an open TODO item reads "Update notebook to use `from ipa.pipeline import build_final_dataframe`", implying the notebook may still use older import paths not consistent with the current public API.
- **`__init__.py` module docstring — example uses invalid IPA**: The docstring example constructs `IPAString("ˈpho.nIks", ...)` using `'I'` (capital I) and `'h'`, which may not be recognized IPA symbols in `ipa_symbols.json` and would raise `ValidationError` if executed. The example should be replaced with a valid IPA transcription.

### Docstring Mismatches to Code

- **`IPAString.coda` — pause detection logic mismatch**: The docstring states that if a `PAUSE` segment is encountered with no consonants counted yet, `'OP'` is returned, otherwise `'SP'`. The code checks `segment == 'O'` (a single-character `'O'`) to distinguish them. Since pause segments in `CustomCharacter` are stored as `'OP'` or `'SP'` (two-character strings), `segment == 'O'` can never be `True`; the branch is dead code. The docstring describes intended behavior correctly, but the implementation has a latent bug that the docstring does not flag.
- **`IPAString.__init__` — duplicate assignment not documented**: Line 82 contains `self.segments = self.segments = self._maximal_munch(processed_string)` (double assignment). Neither the class docstring nor the `__init__` docstring mentions this; it is a code artifact that should be cleaned up silently, but it is worth flagging here.
- **`IPA_CHAR.name()` docstring — return value case inconsistency**: The method docstring says it returns *"The uppercase descriptive name"*, which matches the actual behavior (names are uppercased by `DictionaryLoader`). However the `README.md` example contradicts this by showing a lowercase return (see stale docs item above). The docstring itself is correct; the README example is wrong.
- **`calculate_interstress_duration` — redundant sentinel noted but not documented**: `get_isi_idx` appends `len(df)` as a terminal sentinel to `isi_idx`. `calculate_interstress_duration` then does `zip(isi_idx, isi_idx[1:] + [None])`, creating a trailing `(len(df), None)` pair that is harmlessly collapsed by `range_end = end or len(df)`. The docstring does not explain this interaction, which is confusing to readers of either function.
- **`IPAString.process_string` — geminate handling scope not mentioned**: The docstring says it collapses "runs of identical characters … only when the repeated character is classified as a `'CONSONANT'`" but does not mention that `IPA_CHAR.category()` can raise `ValidationError` for unknown characters during this pre-validation step, which may surface confusing errors before `_validate_string` runs.

### Key Docs Status

- **`README.md`** — Comprehensive. Architecture diagram (Mermaid), CLI flag table, library usage examples, and license are all present. Two example output errors found (segment list mismatch, name case). **Minor update needed.**
- **`AGENTS.md`** — Accurate and up to date. Module reference, layout, environment setup, build/test/lint commands, and guardrails all match the current codebase. **No update needed.**
- **`CONTRIBUTING.md`** — Thorough for most workflows. Missing documentation for `save_language_config` / `append_custom_char` and the `patch_update_1_completed.md` sweep log. **Minor update needed.**
- **`data/language_settings/README.md`** — TOML schema reference, field descriptions, and loading examples are accurate and detailed. Directory contents table lists three files that no longer exist on disk. **Update needed.**
- **`TODO.md`** — Concise and current. Completed items are retained by convention. No stale active items. **No update needed.**

## Reviewer Sweep

Status: Needs fixes

### Risks and Edge Cases in Recent Changes

- **CLI --format produces unwanted files (Medium)**: In `cli.py` lines 156-158, output filenames are set to defaults regardless of the `--format` flag. Then in `_export()` (lines 217-222), both CSV and XLSX are written if format is "both". However, if `--format csv` is specified without `--output-xlsx`, an XLSX file is still created at the default path. This can cause confusion and unexpected file creation. Fix: Only set default paths for formats that will actually be exported.

- **Print statement in pure property (Low)**: In `ipa_string.py` line 188, the coda property uses `print(f"Undefined segment: {segment}")` when encountering an unrecognized segment. This side-effect is inappropriate for a property getter and could interfere with code that captures stdout. Consider removing this print or using proper logging.

- **PAUSE detection logic edge case (Low)**: In `ipa_string.py` line 194, the condition `segment == 'O'` assumes a single-character pause marker. If "OP" is registered as a multi-character custom character with category PAUSE, the reversed iteration would encounter individual segments, and this check may not work as intended for all custom character configurations.

### Code Quality Issues and Follow-ups

- **Dead code (Minor)**: In `ipa_string.py` lines 202-203, there is a commented-out method stub `#def remove_diacritics(self):` that should be removed to keep the codebase clean.

- **Typo in comment (Minor)**: In `ipa_string.py` line 201, the comment says "remove_diacritics" but refers to the `char_only()` method which does more than just remove diacritics (also removes suprasegmentals, tones, accent marks).

### Test and Lint Status

- Tests: **34 passed** - All tests pass successfully.
- Lint (ruff): **All checks passed** - No issues found.
- Type check (mypy): **Success: no issues found** - Incremental type checking passes.

## Fixes Applied

- Updated `IPAString.coda` pause handling to return the pause marker directly; removed stdout print side effect.
- Cleaned `IPAString.__init__` duplicate assignment and removed the dead `remove_diacritics` stub.
- Added a soft warning in `cli.py` when `--config` is omitted.
- Corrected README examples for segments, syllables, and `IPA_CHAR.name()` casing.
- Updated the package docstring example in `src/ipa/__init__.py` to valid IPA and an existing config path.
- Pruned stale legacy file entries from `data/language_settings/README.md`.
