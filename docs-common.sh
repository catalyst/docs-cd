#!/bin/bash
# Settings and functions used by other docs-cd scripts

################################################################################
# Settings
################################################################################

# The swift container that contains the config objects for docs cd
# Objects in this container are expected adhere the the following convention:
# * object name must be the server name that will go into the apache vhost
# * object value must be the git repository hosting the source docs
CONTAINER="https://api.cloud.catalyst.net.nz:8443/swift/v1/docs"

# Home directory where the docs-cd directory lives
DOC_HOME="/home/ubuntu"

# The number of versions of the documentation to preserve in the server for a
# quick fallback to a previous version if required.
BACKUP_VERSIONS=3

# Priorities for logging
ERROR="err"
WARNING="warning"
INFO="info"

################################################################################
# Functions
################################################################################

# Log function
# Inputs:
# $1: priority
# $2-*: message
log() {
  # Tag syslog entries with the name of the running script
  TAG=$(basename "${0}")
  PRIORITY="${1}"
  # Remove priority from argument list, leaving only the message in the stack
  shift
  # Log to syslog and also echo to stdout
  logger -p "${PRIORITY}" -t "${TAG}" $*
  echo $*
}

# Ask Y/n and run function if Y
# Inputs:
# $1: function name
prompt_yn() {
  if [[ "${PROMPT}" != "" ]]; then
    A="Y"
  else
    read A
  fi  
  if [[ "${A}" == "" ]] || [[ "${A}" == "Y" ]] || [[ ${A} == "y" ]]; then
    $*  
  fi  
}

