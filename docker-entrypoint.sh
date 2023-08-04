#!/bin/bash
set -e

# Start memcache on localhost if not using an external service
if [ -z "$MEMCACHIER_SERVERS" ]; then
    echo 'Launching memcache...'

    { service memcached status | grep "not running" ;} && service memcached start || service memcached status
fi

echo "Starting app..."
exec "$@"
