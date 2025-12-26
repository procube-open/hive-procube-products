#!/bin/bash

CURRENT=$(cd $(dirname $0);pwd)

function logging() {
  TS=$(date '+%Y-%m-%d %H:%M:%S')
  echo "$TS $*"
}

function exit_failure() {
  exit 1
}


logging "Start cleanup device_mgmt"
psql -U nsamadmin -h amdb nsam_idp -c "DELETE FROM device_mgmt WHERE expiration < TIMESTAMP 'yesterday';"
RET=$?
if [ $RET -ne 0 ]; then
  logging "Failed to delete records."
  exit_failure
fi

logging "End cleanup device_mgmt"
