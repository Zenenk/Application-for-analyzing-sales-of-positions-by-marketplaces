#!/usr/bin/env bash
# Ожидает, пока заданный хост:порт станет доступен

set -e

HOST="$1"
PORT="$2"
shift 2

TIMEOUT=15
# Разбор флага таймаута, если нужен
while [[ "$1" =~ ^- ]]; do
  case "$1" in
    -t|--timeout)
      TIMEOUT="$2"; shift 2
      ;;
    *) shift ;;
  esac
done

echo "Waiting for $HOST:$PORT (timeout: ${TIMEOUT}s)..."
start=$(date +%s)
while true; do
  if nc -z "$HOST" "$PORT"; then
    echo "$HOST:$PORT is available!"
    break
  fi
  now=$(date +%s)
  if (( now - start >= TIMEOUT )); then
    echo "Timeout after ${TIMEOUT}s: $HOST:$PORT is still not available." >&2
    exit 1
  fi
  sleep 1
done

# Если после -- переданы команды — выполняем их
if [ $# -gt 0 ]; then
  exec "$@"
fi
