Project best practices for the IPA parser codebase. Follow these unless a
change is explicitly requested.

## Imports

- Explicit imports only (no wildcard imports).
- Order: stdlib, third-party, local (`src/ipa/...`).
- One import per line when adding new ones.

## Formatting

- 4-space indentation.
- Reasonable line lengths (no strict formatter enforced).
- No non-ASCII characters unless required for IPA data.

## Naming

- Classes: `CamelCase` (e.g., `IPAString`, `CustomCharacter`).
- Functions/methods: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Use descriptive names for dataframes and lists.

## Error Handling

- Use `ValidationError` from `src/ipa/debug.py` for validation failures.
- Raise exceptions instead of printing errors.
- Validate inputs early (empty strings, invalid symbols).

## IPA and Unicode

- Preserve IPA characters and diacritics; do not normalize them away.
- `CustomCharacter` is the extension mechanism for language-specific IPA.
- `IPAString` relies on maximal munch segmentation; changes to the algorithm
  require careful testing.
- Keep `ipa_symbols.json` in sync with parsing logic when modifying data.

## Pandas

- Keep numeric columns numeric during processing.
- Convert to display strings (e.g., "N/A") only at final export.
- Use `.copy()` when creating `final_df` from slices to avoid
  SettingWithCopyWarning and silent data corruption.
- Scripts and notebooks often mutate dataframes in place; be explicit about it.

## Packaging

- Package is installed from `src/` using setuptools `package-dir`.
- Keep `src/ipa/data/*.json` included via package data.
- Prefer `.venv/bin/python -m pip install -e .` for local development.

## Paths

- This repo runs on macOS and Linux.
- No hardcoded absolute paths inside library code.
- Scripts may use explicit output paths when needed.
- Use absolute paths when exporting outputs from notebooks.

## Testing

- Run tests: `pytest`
- Run one test: `pytest tests/test_ipa_string.py::test_name`
- Lint: `ruff check src tests`
- Types: `mypy src tests`

## Side Effects

- Avoid modifying global state in `src/ipa` unless required.
- When mutating dataframes in place, be explicit about it.
