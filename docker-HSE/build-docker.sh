#!/bin/bash

# rm images
docker system prune -f
docker rmi tsaie79/defectweb-grand:v0.1

export HOST="localhost"
# export HOST="129.10.50.43" db2


# if $HOST is not "localhost" run the following command sh create-host-sshkey.sh
if [ $HOST != "localhost" ]; then
    sh create-host-sshkey.sh
    export PRIVATE_KEY="./id_rsa-for-docker"
fi


docker build --build-arg PRIVATE_KEY=$PRIVATE_KEY -e HOST=$HOST -t tsaie79/defectweb-grand:v0.1 .