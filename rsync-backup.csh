#!/bin/bash

#set -euo pipefail

display_usage() { 
	echo "Usage: $0 [source] [destination] [optional exclude file]\n" 
}

# if less than two arguments supplied, display usage 
if [  $# -le 1 ]; then 
  display_usage
  exit 1
fi 
 
# check whether user had supplied -h or --help . If yes display usage 
if [[ ( $# == "--help") ||  $# == "-h" ]]; then 
  display_usage
  exit 0
fi 

# TODO Allow first arguement to be -n

SOURCE="${1}"         # "/mnt/baobob/baobob-home"
DESTINATION="${2}"    # "/media/jp/Backup"
EXCLUDE_FILE="${3}"   # "/home/jp/exclude-baobob.txt"

# Don't want to deal with : or " in directory names, so don't
if [[ "${SOURCE}" =~ ":" ]]; then
    echo Source \"${SOURCE}\" cannot contain a colon symbol \(:\) Exiting. >&2
    exit 2
fi

if [[ "${SOURCE}" =~ "\"" ]]; then
    echo Source \"${SOURCE}\" cannot contain a double quote \(\"\) Exiting. >&2
    exit 3
fi

if [ ! -d "${SOURCE}" ] ; then
    echo Source \"${SOURCE}\" does not exists. >&2
    exit 4
fi

if test `ls -1A "${SOURCE}" | wc -l` -eq 0; then
   echo Source \"${SOURCE}\" has no contents. Is it mounted? Exiting. >&2
   exit 5
fi

if [[ "${DESTINATION}" =~ ":" ]]; then
    echo Source \"${DESTINATION}\" cannot contain a colon symbol \(:\) Exiting. >&2
    exit 6
fi

if [[ "${DESTINATION}" =~ "\"" ]]; then
    echo Source \"${DESTINATION}\" cannot contain a double quote \(\"\) Exiting. >&2
    exit 7
fi

if [ ! -d "${DESTINATION}" ] ; then
    echo Source \"${DESTINATION}\" does not exists. >&2
    exit 8
fi

DAY=$(date +"%Y-%m-%d")
BACKUP_DIR="$DESTINATION/old/${DAY}"

RSYNC_ARGS=(-r -t --skip-compress --delete -s --itemize-changes --backup  --backup-dir="${BACKUP_DIR}")

EXCLUDE_ARG=()

#TODO check that EXCLUDE_FILE exists if set

if test -n "${EXCLUDE_FILE}"; then
  EXCLUDE_ARG=(--exclude-from ${EXCLUDE_FILE})
fi

echo rsync ${EXCLUDE_ARG[@]} ${SOURCE}
# ${DESTINATION} $BACKUP_DIR

rsync "${RSYNC_ARGS[@]}" "${EXCLUDE_ARG[@]}" "${SOURCE}" "${DESTINATION}"  |  grep -v "skipping non-regular file"



