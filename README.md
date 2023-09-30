# Introduction
This package is for building the websites demonstrating the defect databases with the following DFT calculations:
- Defect calculations with r2SCAN functional
- Defect calculations with HSE functional

# Installation
The packages are containerized with Docker. To install Docker, please refer to the [Docker](https://docs.docker.com/get-docker/).

To build the docker image, run the following command in the terminal:
```bash
sh build-docker.sh
```
- Notice that it will genereate a set of SSH keys for building the SSH tunnel from the container to the database server. Please make sure that the SSH keys are properly generated and the public key is added to the `authorized_keys` on the database server.

# Run the docker image
To run the docker image, run the following command in the terminal:
```bash
sh run-docker.sh
```
- The environment variable `HOST` is used to set the IP address of the database server. Please check the script `run-docker.sh` for more details.
- This will run the docker image in the interactive mode. The container shell will be opened in the background. To access the container shell, run the following command in the terminal:
```bash
docker exec -it CONTAINERID /bin/bash
```
- To check the container ID, run the following command in the terminal:
```bash
docker ps
```

# Build the SSH tunnel from the container to the database server
It is required to build the SSH tunnel from the container to the database server, run the following command in the container shell:
```bash
sh /app/tunnel-db.sh
``` 
- IP address of the database server is required to build the SSH tunnel. It is set by the environment variable `HOST` in the script `run-docker.sh`. Please check the script `tunnel-db.sh` for more details.

# Generate the files for the website
To generate the files for the website, run the following command in the container shell:
```bash
sh /app/generate-rawdata.sh
```
- Notice that it will generate the files in the folder `/usr/local/lib/python3.7/site-packages/flamyngo/static/materials`. If the folder `materials` does not exist, please create it manually.
- To generate the proper files for the website, check the python scripts used in the script `generate-rawdata.sh`. Flags are used to control the functions. For example, the flag `--generate_figures` is used to generate the figures for the website. If the flag is not used, the figures will not be generated. Please check the python scripts for more details.

# Run the website
To run the website, run the following command in the container shell:
```bash
nohup sh run-web.sh > nohup.out 2>&1 &
```
- Notice that one has to at the `/usr/local/lib/python3.7/site-packages/flamyngo/ ` folder to run the website.
- The configuration file `config.yaml` is used to configure the website. Please check the [Flamyngo](https://github.com/materialsvirtuallab/flamyngo) for more details.
- The website will be running at `http://localhost:5000/` for r2SCAN and `http://localhost:5001/` for HSE. To change the port, please check the `config.yaml` file.
