#!/bin/sh
PORT=${PORT:-80}
sed "s/listen 80;/listen $PORT;/g" /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
nginx -g "daemon off;"