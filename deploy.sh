#!/usr/bin/env bash
# deploy.sh — обновить сайт «ПрофЭксперт» на сервере одной командой.
set -euo pipefail
cd "$(dirname "$0")"

[ -f .deploy.env ] || { echo "Нет .deploy.env рядом с deploy.sh"; exit 1; }
source .deploy.env

KEY="${SSH_KEY:-~/.ssh/id_ed25519}"
KEY="${KEY/#\~/$HOME}"

echo "==> Обновляю сайт на сервере ($SERVER_IP:$REMOTE_DIR)"
ssh -i "$KEY" -o BatchMode=yes root@$SERVER_IP "cd $REMOTE_DIR && git pull && pm2 restart $SITE_NAME"

echo "==> Готово! Обновления уже в сети: http://$SERVER_IP"
