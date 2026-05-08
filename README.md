# Memrise-like

Custom interface for Memrise

## Install

### With Docker

* Build the image

      docker-compose build

* Run the container

      docker-compose up -d

### From scratch with postgresql on Heroku

* Install python headers and memcache

      python --version  # 3.6.7

      sudo apt install libpq-dev python3-dev
      sudo apt install memcached libmemcached-dev

* Install dependencies

      pip install -r requirements.txt

* Start the script

      python src/app.py

* Create environment file or environment variables

      DATABASE_URL="postgres://..."
      MEMCACHIER_PASSWORD=""
      MEMCACHIER_SERVERS=""
      MEMCACHIER_USERNAME=""

* Create a database

      heroku config:set SESSION_BACKEND="session.CookieDataStore"
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

It roughly follows the folder [web2py](https://www.web2py.com/books/default/chapter/29/04/the-core#Applications)'s organization

### Front

Location: static

- js6: origin react files
- js: transpiled/served js files
- img: images
- css: css files

## Deployment

See [docs](https://webpy.readthedocs.io/en/latest/deploying.html#nginx-gunicorn)

## Tests

```
pip install tox
tox
tox -e linting
tox -e test

# To get rid of tox's cache:
python -m tox --recreate -e test

# To launch specific pytest (python) tests:
pip install pytest
python -m pytest
python -m pytest tests/test_lang.py
python -m pytest src/tests/test_memrise_get.py -k 'test_memrise_categories' -s -x

# To launch eslint (js files linting):
npm install eslint@4.x babel-eslint@8
npx eslint static/js6 --fix

# To launch ruff
pip install ruff
ruff format
ruff check --fix
```

## Pre-commit

```
pip install pre-commit
pre-commit install
pre-commit run --config .pre-commit-config-lint.yaml

pre-commit run --all-files
git diff ':!static/js/'
```
