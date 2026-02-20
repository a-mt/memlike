#!/bin/bash

# ---
# Create a SASL database used by memcache for authentication
# Location cannot be changed
export SASL_PWDB=/etc/sasldb2
echo "$MEMCACHIER_PASSWORD" | saslpasswd2 -a memcache -c "$MEMCACHIER_USERNAME" -p -f "$SASL_PWDB"
chown memcache:memcache "$SASL_PWDB"

# ---
# Create the SALS config file for memcache
# SASL_CONF_PATH is used when memcache starts with SALS (flag -S)
export SASL_CONF_PATH=/etc/sasl2/memcached.conf

# https://www.binarytides.com/install-and-secure-memcached-1-6-on-ubuntu-23-04/
# https://www.cyrusimap.org/sasl/sasl/options.html
# https://github.com/memcached/memcached/wiki/ReleaseNotes145
# https://web.mit.edu/netbsd/src/gnu/dist/postfix/html/SASL_README.html
mkdir -p $(dirname "$SASL_CONF_PATH")
cat <<EOF > "$SASL_CONF_PATH"
mech_list: plain cram-md5
log_level: 5
db_path: ${SASL_PWDB}
EOF
chown memcache:memcache "$SASL_CONF_PATH"

# ---
# Launch memcache
servers=(${MEMCACHIER_SERVERS//,/ })

for server in ${servers[@]}; do
  if [[ "$server" =~ "127.0.0.1" ]]; then

      port=${server##*:}
      echo "Launching 127.0.0.1:${port:-11211}..."
      memcached -v -u memcache -S -l 127.0.0.1 -p ${port:-11211} -m 64 -d
  fi
done

# Or create config files to use initd service:
#     cp /usr/share/memcached/memcached.conf.default /etc/memcached_EXAMPLE.conf
#     memcached start EXAMPLE

# To start memcache for each existing /etc/memcached_*.conf files:
#     { service memcached status | grep "not running" ;} && service memcached start || service memcached status

# To start memcache manually:
#     ps aux | grep memcache
#     memcached -S -v -u memcache -l 127.0.0.1 -p 11213 -m 64 -d

# To retrieve the envvars created by this script:
#   cat /proc/1/environ | tr '\0' '\n' | sort
#   export $(cat /proc/1/environ | tr '\0' ' ')

# To list users in the SASL database (list of users memcache accepts):
#     sasldblistusers2 -f $SASL_PWDB

# To check accesses:
#     apt update && apt install -y libmemcached-tools
#     memcstat --servers="127.0.0.1:11213" --username=$MEMCACHIER_USERNAME --password=$MEMCACHIER_PASSWORD --binary
# ERR Unable to canonify user and get auxprops =
# Did the container's hostname change (= domain in database)
