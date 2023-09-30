#!/bin/bash


# Run the docker image
docker stop defectweb-hse
docker system prune -f

export HOST="129.10.50.43"

docker run -itd -p 127.0.0.1:5001:5001 -e HOST=$HOST --name defectweb-hse tsaie79/defectweb-hse:v0.1 /bin/bash

