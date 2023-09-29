#!/bin/bash

# rm images
docker system prune -f
docker rmi tsaie79/defectweb:v0.1

# Build the docker image
cd /Volumes/JengStorage/Research/Project/DefectWeb/docker-r2SCAN

sh create-host-sshkey.sh
docker build --build-arg PRIVATE_KEY=id_rsa-for-docker -t tsaie79/defectweb-r2scan:v0.1 .