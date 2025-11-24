#!/usr/bin/env bash
# Simple log viewer for botoy
# Usage: view_log.sh [--follow] [lines]

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/botoy.log"

FOLLOW=false
LINES=200

while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--follow)
      FOLLOW=true
      shift
      ;;
    -n)
      LINES="$2"
      shift 2
      ;;
    *)
      LINES="$1"
      shift
      ;;
  esac
done

if [ ! -f "$LOG_FILE" ]; then
  echo "Log file not found: $LOG_FILE"
  exit 1
fi

if [ "$FOLLOW" = true ]; then
  tail -n "$LINES" -f "$LOG_FILE"
else
  tail -n "$LINES" "$LOG_FILE"
fi
