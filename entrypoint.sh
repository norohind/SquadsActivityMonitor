#!/bin/sh

set -eu


if [ "$IS_WEB" = "true" ]; then
    python3 generate_uswgi_config.py
    exec uwsgi /tmp/uwsgi.ini
fi

exec python main.py $@
