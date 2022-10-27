#!/bin/sh

docker build --tag airbyte_module_client:latest .
kind load docker-image airbyte_module_client:latest --name sm-read
kubectl run my-shell --image airbyte_module_client:latest --image-pull-policy=IfNotPresent -n default --wait
kubectl wait pod --for=condition=ready my-shell -n default
