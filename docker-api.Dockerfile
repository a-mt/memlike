FROM python:3.6-slim-bullseye

ENV PYTHONUNBUFFERED=1

# install system dependencies
RUN apt update \
  && apt install -y gettext wget curl procps \
  && apt install -y memcached libmemcached-dev \
  # cleanup apt cache
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# install app dependencies
ENV APPDIR='/srv'
ENV WWWDIR='/srv/src'

WORKDIR $APPDIR

RUN pip3 install --upgrade pip
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# setup server dependencies
COPY docker-entrypoint.sh ./docker-entrypoint.sh

WORKDIR $APPDIR
EXPOSE 8080

ENTRYPOINT ["bash", "/srv/docker-entrypoint.sh"]
CMD ["python", "src/app.py"]
