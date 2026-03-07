FROM python:3.12-slim-trixie

ENV PYTHONUNBUFFERED=1

# ---
# install system dependencies
# (SASL is used for memcache authentication)
RUN apt update \
  && apt install -y gettext wget curl procps \
  && apt install -y memcached libmemcached-tools libmemcached-dev sasl2-bin \
  && apt install -y python3-pip python3-wheel git \
  # cleanup apt cache
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# ---
# install NVM
ARG NODE_VERSION=12.22  # v20.19.2
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash

# install node
ENV NVM_DIR=/root/.nvm
RUN bash -c "source $NVM_DIR/nvm.sh && nvm install $NODE_VERSION"

# ---
# install app dependencies
ENV APPDIR='/srv'
ENV WWWDIR='/srv/src'

WORKDIR $APPDIR

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# ---
# setup server dependencies
COPY docker-entrypoint.sh ./docker-entrypoint.sh
COPY memcache-start.sh ./memcache-start.sh

EXPOSE 8080

ENTRYPOINT ["bash", "/srv/docker-entrypoint.sh"]
CMD ["python", "src/app.py"]
