#!/bin/bash
BASE=/home/biker/hicdex/hicdex/cron
LIST=$(cat ${BASE}/LEVEL_QUERY.sql | docker exec -i "postgres" psql -t -U dipdup dipdup)
VAL=$(curl -s https://api.tzkt.io/v1/blocks/count)
DIFF=$(($VAL - $LIST))
echo "{\"lag\": $DIFF, \"last_block\": $VAL, \"last_indexed_block\": $LIST}" > ${BASE}/status.json
