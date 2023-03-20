#!/bin/bash

cd ~/sbackup
mkdir -p logs
 ./full-backup.csh  | tee -a logs/tee-log-`date +"%Y-%m-%d"`.log

