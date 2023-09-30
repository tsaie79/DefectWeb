#!/bin/bash


# Run the docker image
docker stop defectweb-r2scan
docker system prune -f

export HOST="129.10.50.43"

docker run -d -p 127.0.0.1:5000:5000 -e HOST=$HOST --name defectweb-r2scan tsaie79/defectweb-r2scan:v0.1

