FROM ubuntu:20.04

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

# CMD ./tunnel-mysql.sh