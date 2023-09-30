#!/bin/bash


# Run the docker image
docker stop defectweb-r2scan
docker system prune -f

export HOST="129.10.50.43"
export RAWDATA_MOUNT_POINT="/home/tsai/defectweb/DefectWeb/docker-r2SCAN/r2SCAN/static/materials"

docker run -itd -p 127.0.0.1:5000:5000 -e HOST=$HOST -v $RAWDATA_MOUNT_POINT:/usr/local/lib/python3.7/site-packages/flamyngo/static/materials --name defectweb-r2scan tsaie79/defectweb-r2scan:v0.1

