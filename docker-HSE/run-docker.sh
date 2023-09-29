#!/bin/bash


# Run the docker image
docker system prune -f
docker run -it --rm -p 127.0.0.1:5000:5000 --name defectweb tsaie79/defectweb-grand:v0.1 bash

