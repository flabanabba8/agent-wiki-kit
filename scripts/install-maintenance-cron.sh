#!/usr/bin/env bash
# Install (or refresh) the weekly maintenance cron entry: Mondays 06:17 local time.
set -euo pipefail
REPO="$(git rev-parse --show-toplevel)"
LINE="17 6 * * 1 cd $REPO && ./scripts/weekly-maintenance.sh >> outputs/.maintenance.log 2>&1  # agent-wiki-kit-weekly"
( crontab -l 2>/dev/null | grep -v 'agent-wiki-kit-weekly' ; echo "$LINE" ) | crontab -
crontab -l | grep agent-wiki-kit-weekly
