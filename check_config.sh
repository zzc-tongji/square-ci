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
	echo Update script not set, required.
	exit 255
fi
UPDATE_SCRIPT=$3

# target
cd ${SCRIPT_PATH}/target/${DIRECTORY} # error code: 1
git remote get-url origin # error code: 127
if [[ ! -f ${TEST_SCRIPT} || ! -x ${TEST_SCRIPT} ]]; then
    exit 2
fi
if [[ ! -f ${UPDATE_SCRIPT} || ! -x ${UPDATE_SCRIPT} ]]; then
    exit 3
fi

# test
cd ${SCRIPT_PATH}/test/${DIRECTORY} # error code: 1
git remote get-url origin # error code: 127
if [[ ! -f ${TEST_SCRIPT} || ! -x ${TEST_SCRIPT} ]]; then
    exit 2
fi
if [[ ! -f ${UPDATE_SCRIPT} || ! -x ${UPDATE_SCRIPT} ]]; then
    exit 3
fi
