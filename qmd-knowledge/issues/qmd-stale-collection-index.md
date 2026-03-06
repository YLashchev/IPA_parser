# Issue #qmd-stale-collection-index

## Summary

The `IPA_parser` QMD collection became stale and stopped tracking newly added
markdown files correctly.

## Root Cause

The collection metadata still reported only 6 indexed markdown files even
though the repository contained 9 markdown files. In that stale state, `qmd get`
could not retrieve newly recorded memory documents, and normal search behavior
was incomplete even after running `qmd embed`.

The exact underlying QMD internal cause was not diagnosed further, but the
observable failure mode was a stale collection index rather than missing files
on disk.

## Fix

Rebuild the collection cleanly:

```bash
qmd collection remove IPA_parser
qmd collection add /Users/yanlashchev/Desktop/IPA_Project/IPA_parser \
  --name IPA_parser --mask "**/*.md"
qmd context add /Users/yanlashchev/Desktop/IPA_Project/IPA_parser \
  "IPA parser project: Python library for IPA phonological analysis, includes project conventions, setup instructions, and knowledge base"
qmd embed
```

**Important:** The correct `collection add` syntax is
`qmd collection add <path> --name <name> --mask <pattern>`. Using positional
arguments without `--name`/`--mask` causes QMD to append the collection name
as a subdirectory (e.g., `.../IPA_parser/IPA_parser`) and find zero files.

After recreating the collection, QMD correctly reported 10 files and both direct
retrieval and search worked for all learning and issue notes.

## Notes

- Symptom: `qmd collection list` file count lagged behind actual repo markdown files
- Symptom: `qmd get` returned `Document not found` for existing new memory files
- Pitfall: using `qmd collection add IPA_parser .` (positional) instead of `--name`/`--mask` flags silently creates the collection at the wrong path
- Recovery is documented in `QMD_WORKFLOW.md`
- 2026-03-06: Reproduced again after first fix; the positional-arg syntax was the root cause of the zero-file recreation. Corrected fix commands above.
