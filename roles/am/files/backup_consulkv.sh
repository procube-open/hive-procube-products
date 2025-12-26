# !/bin/bash

ROOT_KEY=nsam
CERTIFICATE_KEY=certificate
OUTPUT_DIR=consul_kv_bkups
OUTPUT_ARCHIVE=consul_kv_bkups.tar.gz

export_internal() {
  key=$1
  output_file_name=$2
  consul kv export ${key} > ${OUTPUT_DIR}/${output_file_name}.json
}

output_backup_files() {
  key=$1
  output_file_name=${key//\//__}
  export_internal $key ${output_file_name}
}

output_certificate_backup_files() {
  certificate_key_array=($(consul kv get -keys ${ROOT_KEY}/${CERTIFICATE_KEY}/))
  for key in ${certificate_key_array[@]}; do
    output_backup_files ${key}
  done
}

output_single_val() {
  app_name=$1
  declare -a key_name_array=("baseConfig" "authmethod" "ldap" "ntlmConfig" "samlCertificate")
  for key_name in ${key_name_array[@]}; do
    concat_key=${ROOT_KEY}/${app_name}/${key_name}
    output_backup_files ${concat_key}
  done
}

output_multi_val() {
  app_name=$1
  declare -a multi_key_name_array=("dataConnector" "metadataFile" "samlAttribute" "samlAttributeFilter")
  for base_key in ${multi_key_name_array[@]}; do
    declare -a tmp_multi_key_array=($(consul kv get -keys ${ROOT_KEY}/${app_name}/${base_key}/))
    multi_key_array=()
    for tmp_multi_key in ${tmp_multi_key_array[@]}; do
      multi_key=${tmp_multi_key%/}
      multi_key=${multi_key##*/}
      multi_key_array+=( ${multi_key} )
    done
    for multi_key in ${multi_key_array[@]}; do
      concat_key=${ROOT_KEY}/${app_name}/${base_key}/${multi_key}
      output_backup_files ${concat_key}
    done
  done
}

main() {
  echo Start backup consul kv.
  mkdir ${OUTPUT_DIR}
  declare -a app_name_array=()
  declare -a tmp_app_name_array=($(consul kv get -keys ${ROOT_KEY}/))

  for tmp_app_name in ${tmp_app_name_array[@]}; do
    app_name=${tmp_app_name#*/}
    app_name=${app_name%/}
    app_name_array+=( ${app_name} )
  done

  for app_name in ${app_name_array[@]}; do
    if [ ${app_name} = ${CERTIFICATE_KEY} ]; then
       output_certificate_backup_files
       continue       
    fi
    output_single_val ${app_name}
    output_multi_val ${app_name}
  done
  tar cvzf ${OUTPUT_ARCHIVE} ${OUTPUT_DIR}
  rm -rf ${OUTPUT_DIR}
  echo End backup.
}

main
