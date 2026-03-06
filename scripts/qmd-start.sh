#!/bin/bash
# qmd-start.sh — Start the QMD MCP daemon and warm up the embedding model.
#
# On an M1 8GB machine, loading all three GGUF models (~2.1 GB) causes memory
# pressure and system freezes.  This script only warms the embedding model
# (314 MB) which powers vector_search — good semantic understanding at 1/7th
# the memory cost.  deep_search is disabled in OpenCode via opencode.json.
#
# Usage:
#   ./scripts/qmd-start.sh              # start daemon + warm embedding model
#   ./scripts/qmd-start.sh --restart    # stop, start, warmup
#   ./scripts/qmd-start.sh --status     # just print status
#   ./scripts/qmd-start.sh --stop       # stop daemon
#   ./scripts/qmd-start.sh --full       # start + warm ALL models (caution: 2.1 GB)

set -uo pipefail   # no -e: we handle errors explicitly

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

COLLECTION="IPA_parser"
WARMUP_LOG="${TMPDIR:-/tmp}/qmd-warmup.log"

# ── helpers ──────────────────────────────────────────────────────────

status() {
    qmd status 2>&1
}

daemon_running() {
    local out
    out=$(qmd status 2>&1) || true
    echo "$out" | grep -q "MCP:.*running"
}

start_daemon() {
    if daemon_running; then
        echo -e "${GREEN}QMD daemon already running.${NC}"
    else
        echo -e "${YELLOW}Starting QMD MCP daemon...${NC}"
        qmd mcp --http --daemon
        sleep 1
        if daemon_running; then
            echo -e "${GREEN}QMD daemon started.${NC}"
        else
            echo -e "${RED}Failed to start QMD daemon. Check: qmd status${NC}"
            exit 1
        fi
    fi
}

stop_daemon() {
    if daemon_running; then
        echo -e "${YELLOW}Stopping QMD daemon...${NC}"
        qmd mcp stop || true
        sleep 1
        echo -e "${GREEN}Stopped.${NC}"
    else
        echo -e "${YELLOW}QMD daemon is not running.${NC}"
    fi
}

warmup() {
    # Warm the embedding model by sending a vector_search call through the
    # daemon's MCP HTTP endpoint.  This loads only the 314 MB embedding model,
    # keeping memory usage safe on 8 GB machines.
    #
    # If --full is passed, also warm deep_search (loads all 3 models / 2.1 GB).
    # Use --full only when you've closed other heavy apps and have RAM to spare.

    local mode="${1:-light}"
    local MCP_URL="http://localhost:8181/mcp"

    if [ "$mode" = "full" ]; then
        echo -e "${RED}Full warmup: loading ALL 3 models (~2.1 GB). Close other apps to avoid freezes.${NC}"
    else
        echo -e "${YELLOW}Warming embedding model in background (~10-15 s on M1)...${NC}"
    fi
    echo -e "${YELLOW}Progress logged to: ${WARMUP_LOG}${NC}"

    (
        echo "[$(date '+%H:%M:%S')] warmup ($mode): initializing MCP session" > "$WARMUP_LOG"

        # Initialize a fresh MCP session and capture the session ID
        INIT_RESP=$(curl -s -D /dev/stdout -X POST "$MCP_URL" \
            -H "Content-Type: application/json" \
            -H "Accept: application/json, text/event-stream" \
            -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"warmup","version":"0.1"}}}' 2>&1)

        SESSION_ID=$(echo "$INIT_RESP" | grep -i "mcp-session-id" | sed 's/.*: *//' | tr -d '\r')

        if [ -z "$SESSION_ID" ]; then
            # If the daemon already has an active session (e.g. OpenCode is
            # connected), we can't initialize a second one.  Fall back to CLI
            # warmup which loads models in a separate process — this still
            # warms the OS page cache so the daemon loads them faster later.
            echo "[$(date '+%H:%M:%S')] warmup: daemon session occupied, falling back to CLI warmup" >> "$WARMUP_LOG"
            if [ "$mode" = "full" ]; then
                echo "[$(date '+%H:%M:%S')] warmup: running qmd query via CLI (loads all models into page cache)" >> "$WARMUP_LOG"
                qmd query "warmup" -c "$COLLECTION" -n 1 >>"$WARMUP_LOG" 2>&1 || true
            else
                echo "[$(date '+%H:%M:%S')] warmup: running qmd vsearch via CLI (loads embedding model into page cache)" >> "$WARMUP_LOG"
                qmd vsearch "warmup" -c "$COLLECTION" -n 1 >>"$WARMUP_LOG" 2>&1 || true
            fi
            echo "[$(date '+%H:%M:%S')] warmup: CLI fallback done" >> "$WARMUP_LOG"
            exit 0
        fi
        echo "[$(date '+%H:%M:%S')] warmup: session=$SESSION_ID" >> "$WARMUP_LOG"

        # Helper: call an MCP tool through the daemon
        mcp_call() {
            local id="$1"
            local tool="$2"
            local args="$3"
            curl -s -X POST "$MCP_URL" \
                -H "Content-Type: application/json" \
                -H "Accept: application/json, text/event-stream" \
                -H "Mcp-Session-Id: $SESSION_ID" \
                -d "{\"jsonrpc\":\"2.0\",\"id\":$id,\"method\":\"tools/call\",\"params\":{\"name\":\"$tool\",\"arguments\":$args}}" 2>&1
        }

        # vector_search loads only the embedding model (314 MB)
        echo "[$(date '+%H:%M:%S')] warmup: calling vector_search (loads embedding model, 314 MB)" >> "$WARMUP_LOG"
        VS_RESP=$(mcp_call 10 "vector_search" "{\"query\":\"warmup\",\"collection\":\"$COLLECTION\",\"limit\":1}")
        if echo "$VS_RESP" | grep -q '"result"'; then
            echo "[$(date '+%H:%M:%S')] warmup: vector_search OK" >> "$WARMUP_LOG"
        else
            echo "[$(date '+%H:%M:%S')] warmup: vector_search response: $VS_RESP" >> "$WARMUP_LOG"
        fi

        # Only warm deep_search if --full was requested
        if [ "$mode" = "full" ]; then
            echo "[$(date '+%H:%M:%S')] warmup: calling deep_search (loads reranker + query expansion, +1.8 GB)" >> "$WARMUP_LOG"
            DS_RESP=$(mcp_call 11 "deep_search" "{\"query\":\"warmup\",\"collection\":\"$COLLECTION\",\"limit\":1}")
            if echo "$DS_RESP" | grep -q '"result"'; then
                echo "[$(date '+%H:%M:%S')] warmup: deep_search OK" >> "$WARMUP_LOG"
            else
                echo "[$(date '+%H:%M:%S')] warmup: deep_search response: $DS_RESP" >> "$WARMUP_LOG"
            fi
        fi

        echo "[$(date '+%H:%M:%S')] warmup: done — embedding model is hot in daemon" >> "$WARMUP_LOG"
    ) &
    disown
    echo -e "${GREEN}Warmup running in background (PID $!). You can work normally.${NC}"
    echo -e "${GREEN}Check progress:  cat ${WARMUP_LOG}${NC}"
}

# ── main ─────────────────────────────────────────────────────────────

case "${1:-}" in
    --status)
        status
        ;;
    --restart)
        stop_daemon
        start_daemon
        warmup "light"
        ;;
    --stop)
        stop_daemon
        ;;
    --full)
        start_daemon
        warmup "full"
        ;;
    *)
        start_daemon
        warmup "light"
        ;;
esac
