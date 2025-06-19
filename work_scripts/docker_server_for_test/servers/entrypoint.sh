#!/bin/bash
set -e

echo "[ENTRYPOINT] Fixing ownership..."
chown -R victor:victor /home/victor || true

echo "[ENTRYPOINT] Starting SSH daemon..."
exec /usr/sbin/sshd -D