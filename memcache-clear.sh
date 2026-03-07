servers=(${MEMCACHIER_SERVERS//,/ })

for server in ${servers[@]}; do
  if [[ "$server" =~ "127.0.0.1" ]]; then
      echo "Flushing $server..."
      memcflush --servers="$server" --username=$MEMCACHIER_USERNAME --password=$MEMCACHIER_PASSWORD --binary
  fi
done
