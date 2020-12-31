# Memrise-like

Custom interface for Memrise

## Install

* Install python headers and memcache

      python --version  # 3.6.7

      sudo apt install libpq-dev python3-dev
      sudo apt install memcached libmemcached-dev

* Install dependencies

      pip install -r requirements.txt

* Start the script

      python src/app.py

* Create environment file or environment variables

      ```
      DATABASE_URL="postgres://..."
      MEMCACHIER_PASSWORD=""
      MEMCACHIER_SERVERS=""
      MEMCACHIER_USERNAME=""
      ```

* Create a database

      heroku addons:create heroku-postgresql:hobby-dev
      cat init.sql | heroku pg:psql

* Build JS6 to JS6

      npm install
      npm run build