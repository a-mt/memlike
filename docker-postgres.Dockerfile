FROM postgres:14-bullseye

RUN apt-get update \
      && apt-cache showpkg postgresql-contrib-9.6 \
      && apt-get install -y --no-install-recommends \
           postgresql-contrib-9.6 \
      && rm -rf /var/lib/apt/lists/*
