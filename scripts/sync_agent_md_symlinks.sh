#!/usr/bin/env bash
# Creates AGENT.md symlinks pointing to CLAUDE.md in every directory
# that contains a CLAUDE.md file. Idempotent — safe to rerun.
#
# Usage:
#   ./scripts/sync_agent_md_symlinks.sh          # from repo root
#   ./scripts/sync_agent_md_symlinks.sh --dry-run # preview only

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

created=0
skipped=0

while IFS= read -r claude_md; do
    dir="$(dirname "$claude_md")"
    agent_md="$dir/AGENT.md"

    if [[ -L "$agent_md" ]]; then
        # Symlink already exists
        skipped=$((skipped + 1))
        continue
    fi

    if [[ -e "$agent_md" ]]; then
        echo "WARN: $agent_md exists but is not a symlink — skipping"
        skipped=$((skipped + 1))
        continue
    fi

    if $DRY_RUN; then
        echo "Would create: $agent_md -> CLAUDE.md"
    else
        ln -s CLAUDE.md "$agent_md"
        git add "$agent_md" 2>/dev/null || true
        echo "Created: $agent_md -> CLAUDE.md"
    fi
    created=$((created + 1))

done < <(find "$REPO_ROOT" -name CLAUDE.md -not -path '*/.git/*' -not -path '*/.claude/worktrees/*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*')

echo ""
if $DRY_RUN; then
    echo "Dry run complete: $created would be created, $skipped already exist"
else
    echo "Done: $created created, $skipped already exist"
fi
