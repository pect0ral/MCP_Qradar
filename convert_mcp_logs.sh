#!/bin/bash
######
## 2020 12 18
## Mike Piekarski
## 
## ----
## This Script is for use in a scheduled task.
## This script will search for incoming files from MCP and run a conversion on them as they come in.
##

## ------- Set Our Variables
##
## Our Working Directory
## You'll have to override this based on your home directory or wherever you'll be working from
## For this example, it's a user named mcafee's home directory.

## Assumptions ahead is that you have a directory structure of the following:
##
## (working directory defined below)
## ${_WD} ---|
##           |---- in
##           |---- out
##           |____ tmp
##

## Your CSV Files should be shipped from mcafee into the "in" directory
## During conversion, they will live in the "tmp" directory
## Afterwards, they will be moved to the "out" directory for fetching from Qradar

h
_WD="/home/mcafee"
## Script Path
_BIN="${_WD}/bin"
##
_SCRIPT="mcp_convert_with_timestamps.py"




for _file in $( find "${_WD}/in/" -type f -mmin +30 -iname "*.csv" );
do

  _BASE="$( basename ${_file})"
  _OUT="${_WD}/tmp/${_BASE}.log"
  _TMP="${_WD}/tmp/${_BASE}"
  _RUN_LOG="${_WD}/tmp/${_BASE}-conversion.txt"

  echo "Beginning processing for ${_file} and writing to ${_OUT}"
  echo "Moving from ${_file} to ${_TMP}."
  mv "${_file}" "${_TMP}"
  python "${_BIN}/${_SCRIPT}" "${_TMP}" >> "${_OUT}" 2> "${_RUN_LOG}" &

done

for _log in $( find "${_WD}/tmp/" -type f -mmin +10 -iname "*.log" );
do
  sleep 5
  _BASE="$( basename ${_log})"
  _ORIG="${_log//\.log/}"

  _OUT="${_WD}/out/access$( date +%s).log"

  echo "Discovered log file at ${_log}. Processing..."
  echo "Moving file ${_log} to ${_OUT}"

# Updated by MPiekarski on 2020 11 05 to preserve original name
#  mv "${_log}" "${_OUT}"
  mv "${_log}" "${_WD}/out/"

  echo "checking for original ..."
  if [ -f "${_ORIG}" ]; then
    echo "Original file ${_ORIG} found but skipping deletion"
    #echo "Original file ${_ORIG} Found. Deleting ..."
    #rm -f "${_ORIG}"
  else
    echo "Original File not found."
  fi

  echo "Finished processing ${_BASE} file"
  _LINES="$( wc -l ${_OUT} | awk '{ print $1 }')"
  echo "${_LINES} total lines in file ${_BASE}"

  echo "Running cleanup in TMP Directory"
  find "${_WD}/tmp/" -maxdepth 1 -type f -mtime +5 -exec rm -f {}\;

done

for _old in $( find "${_WD}/out/" -type f -mtime +3 -iname "*.log");
do
  echo "Found file ${_old} that is older than 3 days. Removing"
  rm -f "${_old}"
done
