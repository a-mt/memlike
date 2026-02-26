# Memrise-like

Custom interface for Memrise

## Install

### With Docker

* Build the image

      ```
      docker-compose build
      ```

* Run the container

      ```
      docker-compose up -d
      ```

### From scratch with Heroku

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

## Edit JS6 assets

If you need to update files in static/js6:

* Compile JS6 to JS (with watch)

      npm install
      npm run build-dev

## Architecture

### Backend

Location: src

The backend is developed with web.py
([website](https://webpy.org/) / [github](https://github.com/webpy/webpy) / [readthedocs](https://webpy.readthedocs.io/en/latest/))

It roughly follows the folder organization from [web2py](https://www.web2py.com/books/default/chapter/29/04/the-core#Applications)

### Front

Location: static

```
js6: origin react files
js: transpiled/served js files
img: served images
css: served css files
```

## Deploy

See [docs](https://webpy.readthedocs.io/en/latest/deploying.html#nginx-gunicorn)

## Tests

### Backend

```
pip install tox
tox
tox -e flake8
tox -e test

# python -m tox --recreate -e test
# python -m pytest

# pip install pytest; cd src; export WEBPY_ENV=test DEFAULT_LANG=english
# python -m pytest tests/test_lang.py
# python -m pytest src/tests/test_memrise_get.py -k 'test_memrise_categories' -s -x

npm install eslint@4.x babel-eslint@8 --save-dev
eslint js6
```
