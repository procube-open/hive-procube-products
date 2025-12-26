# !/bin/bash
BACKUP_FILE_PATH=consul_kv_bkups/
BACKUP_FILE_ARCHIVE=consul_kv_bkups.tar.gz
declare -A BACKUP_FILE_NAME_MAP=(
  ["__metadataFile__"]=10
  ["__dataConnector__"]=10
  ["__samlAttribute__"]=10
  ["__samlAttributeFilter__"]=10
)

restore_internal() {
  backup_file_path=$1
  sleep_time=$2
  consul kv import "$(cat ${backup_file_path})"
  sleep ${sleep_time}
  rm -f ${backup_file_path}
}


restore() {
  for f in `find ${BACKUP_FILE_PATH} -type f -name "nsam__certificate*"`; do
    restore_internal $f 10
  done
  for key in "${!BACKUP_FILE_NAME_MAP[@]}"; do
    sleep_time=${BACKUP_FILE_NAME_MAP[$key]}
    for f in `find ${BACKUP_FILE_PATH} -type f -name "*${key}*"`; do
      restore_internal $f ${sleep_time}
    done
  done
  # restore other config
  for f in `find ${BACKUP_FILE_PATH} -type f`; do
    restore_internal $f 30
  done
}

main() {
  if [ -f ./${BACKUP_FILE_ARCHIVE} ]; then
    echo "Start restore consul kv."
    tar xzvf ./${BACKUP_FILE_ARCHIVE}
    restore
    systemctl restart wildfly
    rm -rf ${BACKUP_FILE_PATH}
    rm -f ${BACKUP_FILE_ARCHIVE}
    echo "End restore consul kv."
  else
    echo "ERROR: backup file is not exists."
    exit 1
  fi
}

main
