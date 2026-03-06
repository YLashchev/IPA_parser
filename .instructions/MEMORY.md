Purpose: guide the coding agent to use qmd for persistent, project-specific memory stored inside this repository.

See `QMD_WORKFLOW.md` for the high-level operational view of how this project
uses QMD automatically.

## Memory Location

Store all project knowledge inside this repo at:

`qmd-knowledge/`

Recommended structure:

- `qmd-knowledge/learnings/`
- `qmd-knowledge/issues/`

Do not use a home-directory knowledge store for this project unless explicitly instructed.

**Important:** The directory must NOT start with a dot. QMD excludes dot-directories
from indexing, so `.qmd-knowledge/` would never be searchable.

## Project Detection

When working in this repository:

1. Detect the project root with `git rev-parse --show-toplevel`.
2. If that fails, use the current working directory.
3. Use the repository folder name as the default qmd collection name.
4. Use `qmd-knowledge/` inside the project root as the storage location.

## Setup

Before using qmd memory, ensure the local project knowledge base exists.

Run:

    PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
    PROJECT_NAME=$(basename "$PROJECT_ROOT")
    KNOWLEDGE_BASE="$PROJECT_ROOT/qmd-knowledge"

    mkdir -p "$KNOWLEDGE_BASE/learnings"
    mkdir -p "$KNOWLEDGE_BASE/issues"

    ERR_FILE="/tmp/qmd-collection-add-$$.err"
    if qmd collection add "$PROJECT_ROOT" --name "$PROJECT_NAME" --mask "**/*.md" 2>"$ERR_FILE"; then
      echo "Collection created: $PROJECT_NAME"
      rm -f "$ERR_FILE"
    elif grep -qi "already exists" "$ERR_FILE" 2>/dev/null; then
      echo "Collection already exists: $PROJECT_NAME"
      rm -f "$ERR_FILE"
    else
      rm -f "$ERR_FILE"
    fi

    qmd context add "$PROJECT_ROOT" "Knowledge base for $PROJECT_NAME project" 2>/dev/null || true
    qmd embed 2>/dev/null || true

## When To Use Memory

Use qmd memory for:

- Project-specific learnings
- Bug fixes and issue resolution notes
- Known limitations, failure modes, workarounds, and regressions
- Architecture decisions
- Conventions and patterns discovered during work
- Important debugging findings worth preserving across sessions

Do not use qmd memory for:

- Temporary scratch notes
- Obvious implementation details
- General programming knowledge
- Large amounts of duplicated documentation

## Recording Memory

To record knowledge, use the `qmd-knowledge` skill. Load it first:

    skill({ name: "qmd-knowledge" })

Then use `record.sh` via the Bash tool:

    # Record a learning
    .opencode/skills/qmd-knowledge/scripts/record.sh learning "short topic"

    # Record an issue note
    .opencode/skills/qmd-knowledge/scripts/record.sh issue <id> "note text"

    # Record a general note
    .opencode/skills/qmd-knowledge/scripts/record.sh note "note text"

The script creates the file, sets up the directory structure, and runs
`qmd embed` automatically (debounced at 30s).

If recording manually instead of using `record.sh`, create markdown files
directly in `qmd-knowledge/learnings/` or `qmd-knowledge/issues/` and then
run `qmd embed`.

### When to record

Strong signals that something should be recorded:

- "I discovered that..."
- "I learned that..."
- "The fix was..."
- "The root cause was..."
- "We should always..."
- "Do not forget to..."
- "The correct pattern is..."

Record automatically when the lesson is clearly durable and project-specific,
such as a confirmed root cause, a confirmed fix, a new convention, a meaningful
architecture decision, or a reusable gotcha.  Do not wait for the user to ask in
those cases.

Do not record automatically when the note is temporary, obvious, generic, or too
low-value to help future work.

### Learning vs issue

Use a `learning` when the note is mainly a reusable lesson:

- a convention or workflow
- a general debugging takeaway
- an architecture lesson
- a pattern that should be reused later

Use an `issue` when the note is mainly a concrete problem record:

- a confirmed bug
- a known limitation
- a failure mode or regression
- a workaround
- a root cause and fix history for a specific problem

Prefer appending to an existing issue when new investigation, workarounds, or
fixes belong to the same underlying problem.

### Duplicate check before recording

Before creating a new note with `record.sh`, search QMD for similar learnings or
issues first.

- If a near-duplicate already exists, update or append to the existing note.
- If the new information is genuinely distinct, create a new note.
- Prefer avoiding multiple tiny notes that restate the same lesson.

## Searching Memory

When you need project memory, search the project's qmd collection first.
For repo-specific convention/history/"why" questions, treat this as mandatory.

**Hardware note:** This machine is an Apple M1 with 8 GB RAM. The `deep_search`
MCP tool is disabled in OpenCode (`.opencode/opencode.json`) because loading all
3 GGUF models (2.1 GB) causes memory pressure and system freezes. Only
`vector_search` (314 MB embedding model) and `search` (BM25 keyword, no models)
are available via MCP.

Run `./scripts/qmd-start.sh` once per session to start the daemon and warm the
embedding model in the background (~10-15 s). Until warmup finishes, prefer
`search` (instant, no models).

Preferred search patterns via MCP (ordered by quality):

    vector_search  — semantic search, finds related concepts even with different words
    search         — keyword/phrase matching, instant, no models needed

Pass `collection: "IPA_parser"` as a parameter when using MCP tools.

Preferred search patterns via CLI (ordered by quality):

    qmd vsearch -c IPA_parser "concept or natural language question"
    qmd search -c IPA_parser "keyword"
    qmd query -c IPA_parser "your question here"   # CLI only, close other apps first

## Reading Memory

Read specific documents when search results point to them.

Via MCP, use the `get` tool with a file path from search results.

Via CLI:

    qmd get "qmd-knowledge/learnings/2026-03-06-some-topic.md" -c IPA_parser
    qmd get "qmd-knowledge/issues/123.md" -c IPA_parser

## Learning Entry Format

Create a new file in `qmd-knowledge/learnings/` using this format.

Filename: `YYYY-MM-DD-short-topic.md`

Template:

    # Learning: <short title>

    ## Context
    What was being worked on?

    ## Finding
    What was learned?

    ## Why It Matters
    Why is this important for future work?

    ## Action
    What should be done differently next time?

## Issue Entry Format

Create or append to a file in `qmd-knowledge/issues/`.

Filename: `<issue-id>.md`

Template:

    # Issue <issue-id>

    ## Summary
    Short description of the issue.

    ## Root Cause
    What caused it?

    ## Fix
    What resolved it?

    ## Notes
    Any follow-up details, caveats, or commands.

## After Writing Memory

After creating or editing memory files, always refresh the index:

    qmd embed

The `record.sh` script does this automatically. Only run it manually when
editing files directly.

## Agent Behavior

The agent should:

- Search qmd memory before making assumptions about prior project decisions
- Search qmd memory before answering repo-specific convention, history, or
  design-rationale questions
- Suggest recording important learnings when useful discoveries are made
- Record important learnings without asking when the value is clear and durable
- Record issue notes without asking when a concrete problem, limitation,
  workaround, root cause, or fix becomes clear and durable
- Distinguish `learning` vs `issue` correctly instead of storing everything as a
  learning
- Prefer project-specific memory over generic assumptions
- Keep entries concise, factual, and reusable
- Avoid recording duplicate notes when similar memory already exists

When available, prefer the integrated `qmd_memory` tool for search, duplicate
checks, and recording decisions.

## Session Wrap-Up

At the end of a meaningful work session, ask:

- What did we learn?
- Was there a bug fix or debugging insight worth saving?
- Did we establish a new convention or workflow?
- Should any of this be recorded into qmd memory?

If yes, record it and refresh the qmd index.

## Default Assumption

Unless told otherwise, assume:

- project root = current git repo root
- collection name = repo folder name (`IPA_parser`)
- memory location = `qmd-knowledge/` inside the repo
