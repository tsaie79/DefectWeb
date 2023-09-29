# base image for python 3.7

FROM python:3.7.4-slim-buster


# ssh tunneling
ARG PRIVATE_KEY
RUN apt-get update -qq && \
    apt-get install -y -qq openssh-client && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir ~/.ssh && \
  echo "Host *" > ~/.ssh/config && \
  echo "  StrictHostKeyChecking accept-new" >> ~/.ssh/config && \
  echo "  ControlMaster auto" >> ~/.ssh/config && \
  echo "  ControlPath ~/.ssh/%r@%h:%p" >> ~/.ssh/config

COPY $PRIVATE_KEY /root/.ssh/id_rsa

COPY tunnel-db.sh .

# install python
RUN apt-get update && \
    apt-get install -y openssh-server && \
    apt-get install -y git && \ 
    apt-get install -y gcc
    
RUN pip install --upgrade pip

COPY . /app 
WORKDIR /app

RUN pip install numpy
RUN git clone https://github.com/tsaie79/qubitPack.git /usr/local/lib/python3.7/site-packages/qubitPack
# RUN mv qubitPack /usr/local/lib/python3.7/site-packages
WORKDIR /usr/local/lib/python3.7/site-packages/qubitPack
RUN pip install -e .

RUN pip install flamyngo

RUN pip install monty==3.0.2
RUN pip install ipython

# cp r2SCAN to site-packages and rename it to flamyngo
WORKDIR /app
RUN mv r2SCAN /usr/local/lib/python3.7/site-packages
WORKDIR /usr/local/lib/python3.7/site-packages
# rename r2SCAN to flamyngo
RUN rm -rf flamyngo/*
RUN mv r2SCAN/* flamyngo/

# # change the working directory to flamyngo

WORKDIR /usr/local/lib/python3.7/site-packages/flamyngo

EXPOSE 5000
# RUN sh /tunnel-db.sh
# ENTRYPOINT ["flm", "-d", "-c", "config.yaml"]
