#!/bin/bash


# Run the docker image
docker stop defectweb-hse
docker system prune -f

export HOST="129.10.50.43"
export RAWDATA_MOUNT_POINT="/home/tsai/defectweb/DefectWeb/docker-HSE/HSE/static/materials"

docker run -itd -p 127.0.0.1:5001:5001 -e HOST=$HOST -v $RAWDATA_MOUNT_POINT:/usr/local/lib/python3.7/site-packages/flamyngo/static/materials --name defectweb-hse tsaie79/defectweb-hse:v0.1 /bin/bash

