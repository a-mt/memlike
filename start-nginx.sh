FILE="/tmp/app-initialized"

while [[ ! -f "$FILE" ]]
do
    echo 'buildpack=nginx at=app-initialization'
    sleep 1
done
/etc/init.d/nginx start
