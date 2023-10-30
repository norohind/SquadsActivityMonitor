#!/bin/sh

set -eu

echo "Generating uwsgi config"
python3 generate_uswgi_config.py

if [ "$IS_WEB" = "true" ]; then
    echo "Running web"
    exec uwsgi -c /tmp/uwsgi.ini
fi

echo "Running collector"
exec python main.py $@
