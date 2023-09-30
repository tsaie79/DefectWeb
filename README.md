# Introduction
This package is for building the websites demostrating the defect databases with the following DFT calculations:
- Defect calculations with r2SCAN functional
- Defect calculations with HSE functional

# Installation
The packages are containerized with Docker. To install Docker, please refer to the [Docker](https://docs.docker.com/get-docker/).

To build the docker image, run the following command in the terminal:
```bash
sh build_docker.sh
```
- Notice that it will genereate a set of SSH keys for building the SSH tunnel from the container to the database server. Please make sure that the SSH keys are properly generated and the public key is added to the authorized_keys on the database server.

To run the docker image, run the following command in the terminal:
```bash
sh run_docker.sh
```
- Notice that it will login to the container shell directly.

# Generate the files for the website
To generate the files for the website, run the following command in the container shell:
```bash
sh /app/generate_rawdata.sh
```
- Notice that it will generate the files in the folder `/usr/local/lib/python3.7/site-packages/flamyngo/static/materials`. If the folder `materials` does not exist, please create it manually.
- To generate the proper files for the website, check the python scripts used in the script `generate_rawdata.sh`. Flags are used to control the functions. For example, the flag `--generate_figures` is used to generate the figures for the website. If the flag is not used, the figures will not be generated. Please check the python scripts for more details.

# Run the website
To run the website, run the following command in the container shell:
```bash
flm -c config.yaml
```
- Notice that one has to at the `/usr/local/lib/python3.7/site-packages/flamyngo/ ` folder to run the website.
- The configuration file `config.yaml` is used to configure the website. Please check the [Flamyngo](https://github.com/materialsvirtuallab/flamyngo) for more details.
- The website will be running at `http://localhost:5000/`. The port 5000 in the container is mapped to the port 5000 on the host machine. The url `http://localhost:5000/` can be accessed from the host machine.

