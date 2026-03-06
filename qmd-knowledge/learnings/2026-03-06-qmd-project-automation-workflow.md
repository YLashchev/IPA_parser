# Learning: qmd project automation workflow

**Date:** 2026-03-06 02:38:40

## Context

After getting QMD search and recording working for this repository, the next
goal was to make the workflow feel automatic and dependable instead of relying
on remembering ad hoc commands.

## Learning

QMD works best in this repository when it is treated as a project-local utility
layer rather than a manual note-taking side path.

The useful pattern is:

- enforce search-first behavior for repo-specific history, conventions, and
  design-rationale questions
- classify durable memory as either a reusable `learning` or a concrete `issue`
- bias toward recording only durable, project-specific discoveries
- check for duplicates before creating new notes
- keep operational helpers (`qmd-start.sh`, `qmd-doctor.sh`) and guardrails
  (`git-guard`) close to the repo so the workflow is reliable session to session

The integrated OpenCode plugin and `qmd_memory` tool provide a better workflow
than expecting the user or agent to remember `/record-*` commands manually.

## Application

- Keep QMD behavior project-local and documented in `AGENTS.md`,
  `.instructions/MEMORY.md`, and `QMD_WORKFLOW.md`.
- Prefer integrated memory tooling and automatic prompts over manual commands.
- Use `issue` notes for concrete bugs, regressions, limitations, and fixes.
- Use `learning` notes for reusable patterns, conventions, and architecture
  takeaways.
- Run `./scripts/qmd-doctor.sh` when the workflow seems unhealthy.

---

*Recorded by qmd-knowledge skill*
