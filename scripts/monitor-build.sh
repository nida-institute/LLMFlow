#!/bin/bash
# Monitor GitHub Actions build run
# Usage: ./monitor-build.sh [run_id]

RUN_ID="${1:-23166224128}"
INTERVAL=30

echo "Monitoring run $RUN_ID (refreshing every ${INTERVAL}s)..."
echo "Press Ctrl+C to stop."
echo ""

while true; do
  clear
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') — Run $RUN_ID ==="
  echo ""
  gh run view "$RUN_ID"
  STATUS=$(gh run view "$RUN_ID" --json status -q '.status')
  if [[ "$STATUS" == "completed" ]]; then
    echo ""
    CONCLUSION=$(gh run view "$RUN_ID" --json conclusion -q '.conclusion')
    echo "=== Build finished: $CONCLUSION ==="
    if [[ "$CONCLUSION" == "success" ]]; then
      echo ""
      echo "Release assets:"
      TAG=$(gh run view "$RUN_ID" --json headBranch -q '.headBranch' 2>/dev/null || echo "")
      if [[ -n "$TAG" ]]; then
        gh release view "$TAG" --json assets -q '.assets[] | "\(.name)  \(.size) bytes"' 2>/dev/null || echo "(run: gh release list)"
      fi
    fi
    exit 0
  fi
  sleep "$INTERVAL"
done
