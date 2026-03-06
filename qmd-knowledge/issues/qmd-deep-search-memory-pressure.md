# Issue qmd-deep-search-memory-pressure

## Summary

QMD `deep_search` is not safe to use through OpenCode on this Apple M1 machine
with 8 GB RAM because it can trigger severe memory pressure and system freezes.

## Root Cause

`deep_search` loads all three GGUF models used by QMD: the embedding model,
reranker, and query-expansion model. Together they use roughly 2.1 GB. On this
machine that pushes total memory usage too high once macOS, OpenCode, and other
apps are already active, causing swap thrashing and sometimes a hard freeze.

## Fix

- Disabled `qmd_deep_search` in `.opencode/opencode.json`
- Use `vector_search` and `search` through MCP instead
- Warm only the embedding model by default in `scripts/qmd-start.sh`
- Reserve full-model warmup for rare manual use with `--full`

## Notes

- This is a concrete limitation of the current hardware profile.
- Safe defaults are now documented in `AGENTS.md`, `.instructions/MEMORY.md`,
  and `QMD_WORKFLOW.md`.
- The issue matters most for automatic OpenCode workflows because background or
  repeated `deep_search` use would make the system unstable.
