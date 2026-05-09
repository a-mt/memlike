web: ./bin/start-nginx gunicorn -w 4 -p /tmp/app-initialized --log-file - --chdir src -b 0.0.0.0:8080 wsgiapp:wsgiapp
