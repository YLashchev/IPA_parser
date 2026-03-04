# TODO

Backlog items for future refactors and improvements.
Keep this list concise and update it as work is completed.

## Medium Priority
- Convert remaining `data/language_settings/` text files to TOML format.
- Add "remove custom character" to interactive CLI with TOML persistence.
- Add CLI to select language sheet and language settings config. 
- Update notebook to use `from ipa.pipeline import build_final_dataframe`.
- Implement grapheme-cluster aware segmentation for tie bars/combining marks.


## Low Priority

## Completed
- Restructure `data/` directory: `unprocessed/` for input, `processed/` for output.
- Auto-name output files with `YYYY-MM-DD` prefix and `_auto` suffix.
- Add `--format` CLI flag for csv/xlsx/both output selection.
- Declutter repo: remove orphan artifacts, update `.gitignore`.
- Add `.xlsx` and `~$*.xlsx` outputs to `.gitignore` or move exports to `data/`.
- Fix ranking key typo: `DIPHTONG` -> `DIPHTHONG` (code only).
- Add core unit tests for `IPA_CHAR`, `CustomCharacter`, and `IPAString`.
- Extract notebook pipeline logic into reusable library functions.
- Add a CLI entry point with `ipa-parser` console command.
- Add interactive CLI menu for word inspection and config updates.
- Add TOML language config support (`load_language_config`, `save_language_config`).
- Migrate data source from `IPA_Table.json` to `ipa_symbols.json`.
- Reorganize to `src/ipa/` layout with lowercase package name.
- Document the `ipa_symbols.json` schema and validation expectations.
- Full documentation overhaul (README, CONTRIBUTING, language settings README, docstrings).
