#!/bin/bash

echo "Starting MongoDB in Network 'test-network'"

docker network create test-network 2> /dev/null

docker run --rm -t --name mongodb -p 27017:27017 --network test-network \
  -e MONGO_INITDB_ROOT_USERNAME=testuser -e MONGO_INITDB_ROOT_PASSWORD=testpassword \
-d mongo
