#!/bin/bash

set -e
SCRIPT_PATH="$( cd "$(dirname "$0")" ; pwd -P )"

# input
if [[ -z $1 ]]; then
	echo Directory not set, required.
	exit 255
fi
DIRECTORY=$1
if [[ -z $2 ]]; then
	echo Test script not set, required.
	exit 255
fi
TEST_SCRIPT=$2
if [[ -z $3 ]]; then
	echo Repo not set, required.
	exit 255
fi
REPO=$3
if [[ -z $4 ]]; then
	echo Branch name not set, required.
	exit 255
fi
BRANCH_NAME=$4

# set environment
cd ${SCRIPT_PATH}/test/${DIRECTORY}
git checkout master
git pull origin master:master
git checkout -b test
git pull ${REPO} ${BRANCH_NAME}

# test
set +e
./${TEST_SCRIPT}
RESULT=$?
set -e

# reset environment
git checkout master
git branch -D test
git remote update --prune

# exit
exit ${RESULT}
