#!/usr/bin/env bash
# salaryfree.in uptime healthcheck
# Runs every 2 min via systemd timer.
# Sends Telegram alert on DOWN, recovery message when site comes back.

set -euo pipefail

source /home/uma/.config/salaryfree/telegram.conf

HEALTH_URL="https://salaryfree.in/health/"
FLAG_FILE="/tmp/sf_site_was_down"
TIMEOUT=15

send_telegram() {
  curl -s --max-time 10 \
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=$1" \
    --data-urlencode "parse_mode=Markdown" \
    > /dev/null
}

# Check the health endpoint
HTTP_CODE=$(curl -s -o /tmp/sf_health_body --write-out "%{http_code}" \
  --max-time "${TIMEOUT}" "${HEALTH_URL}" 2>/dev/null || echo "000")

BODY=$(cat /tmp/sf_health_body 2>/dev/null || echo "")

if [[ "${HTTP_CODE}" == "200" ]]; then
  # Site is UP
  if [[ -f "${FLAG_FILE}" ]]; then
    # Was down — send recovery alert
    DOWNTIME=$(( ($(date +%s) - $(cat "${FLAG_FILE}")) / 60 ))
    send_telegram "✅ *salaryfree.in is back up* 🎉
Down for ~${DOWNTIME} min. All systems normal."
    rm -f "${FLAG_FILE}"
  fi
else
  # Site is DOWN
  if [[ ! -f "${FLAG_FILE}" ]]; then
    # First failure — record timestamp and alert
    date +%s > "${FLAG_FILE}"
    send_telegram "🔴 *salaryfree.in is DOWN*
Status: \`${HTTP_CODE}\`
Time: $(date '+%Y-%m-%d %H:%M IST')

Response: \`${BODY:0:200}\`"
  fi
  # If flag already exists, site is still down — don't spam
fi
