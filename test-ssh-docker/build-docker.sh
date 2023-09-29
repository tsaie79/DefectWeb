#!/bin/bash

# rm image
docker rmi -f docker-ssh-tunnel:latest
docker system prune -f

# build image
docker build --build-arg PRIVATE_KEY=id_rsa-for-docker -t docker-ssh-tunnel .