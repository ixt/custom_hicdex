#!/bin/bash

BACKUP=$1
PROJECT_PATH=/home/biker/hicdex/hicdex
REORG_FILE=/home/biker/hicdex/infos/reorg.txt
METAS_PATH=/home/biker/hicdex/hicdex-metadata

if test -f "${BACKUP}"; then
  echo "Stopping idx"
  docker stop idx
  echo "Stopping hicdex"
  docker stop hicdex
  echo "Stopping hasura"
  docker stop hasura
  echo "Stopping backup"
  docker stop backup

  # not needed anymore as we store proper key in meta to invalidate cache
  # echo "Cleanup metas after ${min_date}"
  # date=`echo ${BACKUP} | cut -d '-' -f2`
  # time=`echo ${BACKUP} | cut -d '-' -f3`
  # min_date="${date:0:4}-${date:4:2}-${date:6:2} ${time:0:2}:${time:2:2}:${time:4:2}"

  # find $METAS_PATH/tokens -type f -newermt "${min_date}" -ls -exec rm -f {} \;
  # find $METAS_PATH/subjkts -type f -newermt "${min_date}" -ls -exec rm -f {} \;

  echo "Start Restoring ${BACKUP}"
  # recreate schema if needed
  # echo "CREATE SCHEMA IF NOT EXISTS hic_et_nunc;SET search_path TO hic_et_nunc;"  | docker exec -i postgres psql --username=dipdup --dbname=dipdup -W
  zcat $BACKUP | docker exec -i postgres psql --username=dipdup --dbname=dipdup -W

  echo "Restart hicdex"
  docker-compose --project-directory $PROJECT_PATH up -d

  rm -f $REORG_FILE
  $PROJECT_PATH/cron/check.sh
  echo "End restoring ${BACKUP}"
else
  echo "Backup not found !! Try again"
fi