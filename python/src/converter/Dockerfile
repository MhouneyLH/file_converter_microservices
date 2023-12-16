FROM python:3.12-slim-bullseye

# all in one command so that we only have one layer
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential ffmpeg python3-pip pkg-config \
    && pip3 install --no-cache-dir --upgrade pip

WORKDIR /app

# install dependencies
COPY ./requirements.txt /app
RUN pip3 install --no-cache-dir --requirement /app/requirements.txt

# copy source code from host to container
COPY . /app

# kein Port wird exposed, weil dieser Service nur Messages konsumiert (intern)

CMD ["python3", "consumer.py"]