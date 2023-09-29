#!/bin/bash

# rm images
docker system prune -f
docker rmi tsaie79/defectweb-grand:v0.1

export HOST="localhost"
# export HOST="129.10.50.43" db2

# if $HOST is not "localhost" run the following command sh create-host-sshkey.sh
if [ $HOST != "localhost" ]; then
    sh create-host-sshkey.sh
    docker build --build-arg PRIVATE_KEY=id_rsa-for-docker -t tsaie79/defectweb-grand:v0.1 .
else
    docker build -t tsaie79/defectweb-grand:v0.1 .
fi



