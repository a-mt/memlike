#!/bin/bash
set -e

# Start memcache on localhost if not using an external service
if [ -z "$MEMCACHIER_SERVERS" ]; then
    echo 'Launching memcache...'

    { service memcached status | grep "not running" ;} && service memcached start || service memcached status
fi

# loads NVM
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && source "$NVM_DIR/bash_completion"

echo "Launching entrypoint..."
exec "$@"