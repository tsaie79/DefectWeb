# base image for python 3.7

FROM python:3.7-slim-buster

# install pip 

RUN apt-get update && apt-get install -y python3-pip

# install git

RUN apt-get install -y git

# install dependencies based on requirements.txt

COPY requirements.txt /tmp/requirements.txt
# update pip
RUN pip install --upgrade pip
RUN pip install -r /tmp/requirements.txt

# copy the source code to the container

COPY . /app
WORKDIR /app

# run the application and expose port 5000

EXPOSE 5000

# cp r2SCAN to site-packages and rename it to flamyngo

RUN cp -r r2SCAN /usr/local/lib/python3.7/site-packages/flamyngo

# change the working directory to flamyngo

WORKDIR /usr/local/lib/python3.7/site-packages/flamyngo

# run the application by flm -c config.yaml

CMD ["flm", "-c", "config.yaml"]