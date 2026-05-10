#!/bin/bash
set -e

# Start memcache on localhost if not using an external service
# /usr/share/memcached/memcached.conf.default
# /etc/memcached.conf
# /etc/init.d/memcached start NAME -> /etc/memcached_*.conf
if [[ -z "$MEMCACHIER_SERVERS" || "$MEMCACHIER_SERVERS" =~ "127.0.0.1" ]]; then
    echo "Launching memcache..."
    source /srv/memcache-start.sh
fi

# loads NVM
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && source "$NVM_DIR/bash_completion"

if [[ "$USE_NGINX" == "1" ]]; then
    bash "$APPDIR/start-nginx.sh" &
fi

if [[ ! -d "/var/log/gunicorn" ]]; then
    mkdir /var/log/gunicorn
fi

echo "Launching entrypoint..."
exec "$@"
