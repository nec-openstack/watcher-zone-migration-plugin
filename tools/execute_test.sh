#!/usr/bin/env bash

set -eu
export LC_ALL=C

OS_WATCHER_AUDIT_INPUT_FILE=${1:-$OS_WATHER_AUDIT_INPUT_FILE}
OS_WATCHER_GOAL_NAME=${OS_WATCHER_GOAL_NAME:-"zone_migration"}
OS_WATCHER_GOAL_NAME=${2:-$OS_WATCHER_GOAL_NAME}
OS_WATCHER_STRATEGY_NAME=${OS_WATCHER_STRATEGY_NAME:-"parallel_migration"}
OS_WATCHER_STRATEGY_NAME=${3:-$OS_WATCHER_STRATEGY_NAME}

params=`cat ${OS_WATCHER_AUDIT_INPUT_FILE}`
params=`echo ${params}`

watcher audit create \
        -g ${OS_WATCHER_GOAL_NAME} \
        -s ${OS_WATCHER_STRATEGY_NAME} \
        -p params="${params}"
