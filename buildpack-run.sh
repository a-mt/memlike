#----------------------------------------------------------
# Upload files using heroku config vars (text only)
#----------------------------------------------------------
# To upload ".ca03e24da771.json":
# heroku config:set UPLOAD1=$(printf ".ca03e24da771.json=%q" `cat .ca03e24da771.json`)
#
# To list distant files:
# heroku run ls -la
#
# To remove ".ca03e24da771.json":
# heroku config:set UPLOAD1=".ca03e24da771.json="
#
# To clear out configs (will keep the uploaded file):
# heroku config:unset UPLOAD1
#----------------------------------------------------------

IFS=$' \t\n'
for file in $ENV_DIR"/UPLOAD"*; do

    upload=$(cat $file)
    filename=${upload%%=*}
    content=${upload#*=}

    echo $content | xargs > "$filename"

    # The file only contains EOF, delete it
    find "$filename" -size 1 -delete
done

#----------------------------------------------------------
# Download Google Cloud SQL Proxy
#----------------------------------------------------------

wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy