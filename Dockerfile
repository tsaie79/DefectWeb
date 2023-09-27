# create a image based on python:3.7.3-alpine

FROM python:3.7.3-alpine

# install git, less and vim

RUN apk update && apk add git less vim

# install dependencies for cython

RUN apk update && apk add make automake gcc g++ subversion python3-dev

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