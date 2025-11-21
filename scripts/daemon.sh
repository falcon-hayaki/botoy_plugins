#!/usr/bin/env bash
# Daemon control script for botoy
# Usage: daemon.sh start|stop|restart|status

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOG_DIR="$ROOT_DIR/logs"
RUN_DIR="$ROOT_DIR/run"
PID_FILE="$RUN_DIR/botoy.pid"
LOG_FILE="$LOG_DIR/botoy.log"
MAX_SIZE=$((500*1024))
MAX_BACKUPS=5
PYTHON_CMD="python3 $ROOT_DIR/bot.py"

mkdir -p "$LOG_DIR" "$RUN_DIR"

rotate_logs() {
  if [ ! -f "$LOG_FILE" ]; then
    return
  fi
  local size
  size=$(stat -c%s "$LOG_FILE" || echo 0)
  if [ "$size" -le "$MAX_SIZE" ]; then
    return
  fi

  # rotate: botoy.log.4 -> botoy.log.5, ..., botoy.log -> botoy.log.1
  for ((i=MAX_BACKUPS-1;i>=1;i--)); do
    if [ -f "$LOG_FILE.$i" ]; then
      next=$((i+1))
      if [ "$next" -gt "$MAX_BACKUPS" ]; then
        rm -f "$LOG_FILE.$i"
      else
        mv "$LOG_FILE.$i" "$LOG_FILE.$next"
      fi
    fi
  done
  if [ -f "$LOG_FILE" ]; then
    mv "$LOG_FILE" "$LOG_FILE.1"
  fi
}

is_running() {
  if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

start() {
  if is_running; then
    echo "Already running (pid $(cat "$PID_FILE"))"
    return 0
  fi
  rotate_logs
  echo "Starting botoy..."
  nohup $PYTHON_CMD >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  sleep 0.2
  if is_running; then
    echo "Started, pid $(cat "$PID_FILE")"
  else
    echo "Failed to start, check $LOG_FILE"
    return 1
  fi
}

stop() {
  if ! is_running; then
    echo "Not running"
    return 0
  fi
  pid=$(cat "$PID_FILE")
  echo "Stopping pid $pid..."
  kill "$pid" || true
  # wait up to 10s
  for i in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 0.5
  done
  if kill -0 "$pid" 2>/dev/null; then
    echo "Force killing $pid"
    kill -9 "$pid" || true
  fi
  rm -f "$PID_FILE"
  echo "Stopped"
}

status() {
  if is_running; then
    echo "Running (pid $(cat "$PID_FILE"))"
  else
    echo "Not running"
  fi
}

case ${1:-} in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop || true
    start
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 2
    ;;
esac
