#!/bin/bash

set -uo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
KNOWLEDGE_DIR="$ROOT_DIR/qmd-knowledge"
COLLECTION="IPA_parser"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok() {
    printf "%b%s%b\n" "$GREEN" "$1" "$NC"
}

warn() {
    printf "%b%s%b\n" "$YELLOW" "$1" "$NC"
}

fail() {
    printf "%b%s%b\n" "$RED" "$1" "$NC"
}

check_command() {
    local name="$1"
    if command -v "$name" >/dev/null 2>&1; then
        ok "Found command: $name"
    else
        fail "Missing command: $name"
        return 1
    fi
}

check_path() {
    local path="$1"
    if [ -e "$path" ]; then
        ok "Found: $path"
    else
        fail "Missing: $path"
        return 1
    fi
}

echo "QMD Doctor"
echo "Project root: $ROOT_DIR"
echo

STATUS=0

check_command qmd || STATUS=1
check_path "$ROOT_DIR/scripts/qmd-start.sh" || STATUS=1
check_path "$ROOT_DIR/.opencode/plugins/qmd-automation.js" || STATUS=1
check_path "$ROOT_DIR/.opencode/plugins/git-guard.js" || STATUS=1
check_path "$ROOT_DIR/.instructions/MEMORY.md" || STATUS=1

if [ -d "$KNOWLEDGE_DIR" ]; then
    ok "Knowledge directory present: $KNOWLEDGE_DIR"
else
    warn "Knowledge directory missing: $KNOWLEDGE_DIR"
    STATUS=1
fi

if [ -d "$KNOWLEDGE_DIR/learnings" ]; then
    ok "Learnings directory present"
else
    warn "Missing learnings directory"
    STATUS=1
fi

if [ -d "$KNOWLEDGE_DIR/issues" ]; then
    ok "Issues directory present"
else
    warn "Missing issues directory"
    STATUS=1
fi

echo
if qmd status >/tmp/qmd-doctor-status.$$ 2>&1; then
    ok "qmd status succeeded"
    if grep -q "MCP:   running" /tmp/qmd-doctor-status.$$; then
        ok "QMD daemon is running"
    else
        warn "QMD daemon is not running"
        STATUS=1
    fi

    if grep -q "$COLLECTION" /tmp/qmd-doctor-status.$$; then
        ok "Collection registered: $COLLECTION"
    else
        warn "Collection not visible in qmd status: $COLLECTION"
        STATUS=1
    fi
else
    fail "qmd status failed"
    STATUS=1
fi
rm -f /tmp/qmd-doctor-status.$$

echo
if [ -d "$KNOWLEDGE_DIR" ]; then
    if (cd "$KNOWLEDGE_DIR" && qmd embed >/tmp/qmd-doctor-embed.$$ 2>&1); then
        ok "qmd embed succeeded"
    else
        warn "qmd embed failed"
        STATUS=1
    fi
    rm -f /tmp/qmd-doctor-embed.$$
fi

echo
if [ "$STATUS" -eq 0 ]; then
    ok "QMD doctor checks passed"
else
    warn "QMD doctor found one or more problems"
fi

exit "$STATUS"
