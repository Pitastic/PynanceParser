#!/bin/bash

SCRIPT_PATH="`dirname \"$0\"`"
ROOT_PATH="`( cd \"$SCRIPT_PATH\" && pwd )`"
cd $ROOT_PATH/../

docker network create test-network 2> /dev/null

docker run --network test-network -t --rm -v .:/app test_app "$@"