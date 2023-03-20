#!/bin/bash

#set -euo pipefail

cd /home/xx/sbackup

ONERR="python3.9 python/TextOnError.py -n"
ONERR=""

# Use "sudo visudo" to tell sudo not to ask
# for a password for the mount -a command.
# and then add the below to the end of the file:
# username ALL=(root) NOPASSWD: /bin/mount -a
# Using the username that will run the backup
sudo mount -a

# Want to stop if these source directories are
# empty.
MOUNTS="/mnt/baobob-home
/mnt/bonsai-home"

for f in $MOUNTS
do
    ${ONERR} mountpoint "$f"

    if [ `ls -a1 "$f" | wc -l` -le 2 ] ; then
      echo "Directory is empty $f, check if mounted"
      ${ONERR} --always -m "Directory is empty $f, check if mounted"
      exit 10
    fi
    # $f has content
done

${ONERR} mountpoint /media/xx/Backup/
${ONERR} mountpoint /mnt/baobob-home
${ONERR} mountpoint /mnt/bonsai-home

${ONERR} ./rsync-backup.csh /mnt/baobob-home /media/xx/Backup exclude-baobob.txt

${ONERR} ./rsync-backup.csh /mnt/bonsai-home /media/xx/Backup exclude-bonsai.txt

echo Collapse /media/xx/Backup/old/
${ONERR} python3.9 python/Collapse.py -v /media/xx/Backup/old/

echo Dup Check -p /media/xx/Backup/ -s /media/xx/Backup/old/
${ONERR} python3.9 python/DuplicateDelete.py -v -s /media/xx/Backup/old/ -p /media/xx/Backup/

echo Canary Check
${ONERR} md5sum --quiet -c canary.md5

