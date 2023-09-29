#!/bin/bash


# Run the docker image
docker stop defectweb 
docker system prune -f

export HOST="129.10.50.43"

docker run -it --rm -p 127.0.0.1:5000:5000 -e HOST=$HOST --name defectweb tsaie79/defectweb-grand:v0.1 bash

