# Memrise-like

## Install

### Create a Google SQL Instance

* Access [Google Cloud Console](https://console.cloud.google.com/)  
  * If you don't have an account, you can have a [free trial](https://cloud.google.com/free/) (300$ credit for free)
  * Choose a project or Create a new one
  * In the left panel, go to `Storage > SQL`
  * `Create an instance`. Choose MySQL, Second Generation
  * In the `Overview` tab of the instance's details, take note of the Instance connection name
  * Go to the tab `Users` and create a MySQL user account
  * Go to the tab `Databases` and create a MySQL database

* Enable [Cloud SQL Administration API](https://console.cloud.google.com/flows/enableapi?apiid=sqladmin&redirect=https://console.cloud.google.com&_ga=2.131986251.-557403291.1515535598) for your project
* Enable [Cloud SQL API](https://console.cloud.google.com/apis/api/sql-component.googleapis.com/overview) for your project
* Go to [service accounts](https://console.cloud.google.com/iam-admin/serviceaccounts/?_ga=2.61265896.-557403291.1515535598)
  * Select your project
  * `Create service account`
  * Select role `Cloud SQL > Cloud SQL Client`
  * Check `Furnish a new private key > JSON`
  * `Create`. Download the JSON file

* Server-side:
  * Upload your JSON file
  * Create a `.env` file: (replace with your own MySQL credentials)

        DATABASE_URL="mysql+pymysql://<MYSQL_NAME>:<MYSQL_USER>@127.0.0.1/<MYSQL_DB>"

### Run

* Install python headers and memcache

      sudo apt-get install python2.7-dev
      sudo apt-get install memcached libmemcached-dev

* Install dependencies

      pip install -r requirements.txt

* Download Google Cloud SQL Proxy

      wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
      chmod +x cloud_sql_proxy

* Start your proxy (replace with your own Instance connnection name and JSON file)

      ./cloud_sql_proxy -instances=<INSTANCE_CONNECTION_NAME>=tcp:3306 -credential_file=<JSON_FILE>

* Start the script

      python src/app.py

[Source](https://cloud.google.com/sql/docs/mysql/connect-admin-proxy)

### Deploy on Heroku

Update `Procfile` with your own Instance connection name and JSON file

``` bash
heroku login
heroku create
heroku buildpacks:add https://github.com/weibeld/heroku-buildpack-run.git
```

``` bash
# Put your own JSON filename (Google Cloud SQL Service Account)
JSON=".ca03e24da771.json"
heroku config:set UPLOAD1=$(printf "$JSON=%q" `cat $JSON`)
```

``` bash
git push heroku master
heroku ps:scale web=1
heroku config:unset UPLOAD1
heroku open
```