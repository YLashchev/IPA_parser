# QMD Workflow

QMD is this repo's persistent memory layer for OpenCode.

## What Is Automatic
- Search QMD first for repo-specific history, conventions, and "why" questions
- Prefer duplicate checks before writing new notes
- Bias classification toward `learning` vs `issue`
- Nudge wrap-up at the end of meaningful sessions

## What To Record
- `learning`: reusable convention, workflow, architecture lesson, or debugging takeaway
- `issue`: bug, regression, limitation, failure mode, workaround, root cause, or fix history

Prefer `issue` when a specific problem was investigated or fixed.

## Main Files
- `.opencode/plugins/qmd-automation.js` - search-first policy and `qmd_memory`
- `.opencode/plugins/git-guard.js` - git safety guardrails
- `.instructions/MEMORY.md` - detailed recording rules
- `AGENTS.md` - repo-level agent behavior
- `scripts/qmd-start.sh` - start daemon and warm models
- `scripts/qmd-doctor.sh` - health check

## Operational Checks
Run:

```bash
./scripts/qmd-doctor.sh
```

## Collection Recovery
If new markdown files exist but QMD reports an old file count or cannot retrieve
them, rebuild the collection:

```bash
qmd collection remove IPA_parser
qmd collection add /path/to/IPA_parser \
  --name IPA_parser --mask "**/*.md"
qmd context add /path/to/IPA_parser \
  "IPA parser project: Python library for IPA phonological analysis, includes project conventions, setup instructions, and knowledge base"
qmd embed
```

Important:
- Use `qmd collection add <path> --name <name> --mask <pattern>`
- Do not store memory in a dot-directory; use `qmd-knowledge/`
- `deep_search` stays disabled on this machine; use `search` or `vector_search`
