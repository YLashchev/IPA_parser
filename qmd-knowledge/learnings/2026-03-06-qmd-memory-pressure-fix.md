# Learning: QMD MCP server memory pressure and dot-directory indexing

## Context

Setting up QMD as a persistent knowledge base for the IPA parser project,
accessed via MCP from OpenCode on an Apple M1 with 8 GB RAM.

## Finding

Two critical issues were discovered:

1. **Memory pressure from deep_search:** QMD's `deep_search` (hybrid search)
   loads all three GGUF models into memory simultaneously: embedding (314 MB),
   reranker (639 MB), and query expansion (1.28 GB) -- totaling ~2.1 GB.
   On an 8 GB M1 Mac, this leaves insufficient memory for macOS + OpenCode,
   causing swap thrashing and system freezes that require a hard restart.

2. **Dot-directories excluded from indexing:** QMD uses `fast-glob` with
   `dot: false` and an explicit filter (`qmd.js:1205-1208`) that rejects any
   file path containing a segment starting with `.`. The knowledge base was
   originally stored in `.qmd-knowledge/`, which meant **none of the knowledge
   files were ever indexed or searchable**. The entire knowledge workflow was
   silently broken.

## Why It Matters

- The memory issue makes full hybrid search unusable on 8 GB machines without
  careful orchestration. This is the same class of problem reported in
  openclaw/openclaw#8786 for CPU-only VPS instances.
- The dot-directory issue means any QMD knowledge base stored in a hidden
  directory (a common convention for config/data dirs) will silently fail to
  be indexed. There is no warning from QMD about this.

## Action

- Disabled `deep_search` in OpenCode (`"qmd_deep_search": false` in
  `.opencode/opencode.json`). Only `vector_search` (314 MB) and `search`
  (BM25, no models) are available via MCP.
- Updated `scripts/qmd-start.sh` to only warm the embedding model by default.
  Added `--full` flag for rare full-model warmup.
- Renamed `.qmd-knowledge/` to `qmd-knowledge/` so QMD can index the files.
- Updated all references in `record.sh`, `MEMORY.md`, and `AGENTS.md`.
- Wrote the `SKILL.md` for the `qmd-knowledge` skill (was empty/broken).
