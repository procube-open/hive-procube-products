#!/bin/bash

CURRENT=$(cd $(dirname $0);pwd)
USERS_SEEDS_CSV="/root/users_seeds.csv"
USER_SEED_IDM_CSV="/root/user_seed.csv"
IDM_CSV_DIR="/home/prov/update_seedtime"

function logging() {
  TS=$(date '+%Y-%m-%d %H:%M:%S')
  echo "$TS $*"
}

function exit_failure() {
  exit 1
}


logging "Start users_seeds transfer"

logging "Cleanup."
rm ${USERS_SEEDS_CSV} ${USER_SEED_IDM_CSV} -f

logging "Start export csv from users_seeds table."
psql -U nsamadmin -h amdb nsam_idp -c "COPY users_seeds TO STDOUT WITH CSV FORCE QUOTE *" > ${USERS_SEEDS_CSV}
RET=$?
if [ $RET -ne 0 ]; then
  logging "Failed to export csv from psql."
  exit_failure
fi

logging "Start convert csv for IDM2."
python ${CURRENT}/convert_users_seeds_csv.py ${USERS_SEEDS_CSV} ${USER_SEED_IDM_CSV}
RET=$?
if [ $RET -ne 0 ]; then
  logging "Failed to convert csv."
  exit_failure
fi

logging "Start transfer csv to idm"
scp -o "StrictHostKeyChecking no" ${USER_SEED_IDM_CSV} prov@idm:${IDM_CSV_DIR}/

logging "End users_seeds transfer"
