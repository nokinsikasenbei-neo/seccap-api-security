#!/bin/bash

RETRIES=20

until (curl --output /dev/null --silent --fail http://localhost:7000/healthcheck) || [ $RETRIES -eq 0 ]; do
  echo "Waiting for API server to start, $RETRIES more times..."
  sleep 5
  RETRIES=$((RETRIES-1))
done

if [ $RETRIES -eq 0 ]; then
  echo "API server didn't start in time."
  exit 1
fi
