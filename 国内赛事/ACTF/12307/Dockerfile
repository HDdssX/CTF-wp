FROM node:24-bookworm-slim AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM debian:forky-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      mariadb-client \
      mariadb-server \
      nginx \
      nodejs \
      python3 \
      python3-pymysql \
      redis-server \
      supervisor \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -r -M -s /usr/sbin/nologin rail && \
    useradd -r -M -s /usr/sbin/nologin settle

WORKDIR /app

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY services /app/services
COPY --from=frontend-build /frontend/dist /app/frontend/dist
COPY --chmod=0600 --chown=root:root flag /flag

RUN chown -R root:root /app /etc/nginx/nginx.conf && \
    find /app -type d -exec chmod 0755 {} + && \
    find /app -type f -exec chmod 0644 {} +

RUN cat > /etc/supervisor/conf.d/services.conf <<'EOF'
[supervisord]
nodaemon=true
user=root
logfile=/tmp/supervisord.log
pidfile=/run/supervisord.pid

[program:redis]
command=/bin/sh -lc 'exec /usr/bin/redis-server --bind 127.0.0.1 --protected-mode yes --save "" --appendonly no --logfile ""'
user=redis
priority=10
autostart=true
autorestart=true
startsecs=0
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:mariadb]
command=/usr/sbin/mariadbd --user=mysql --bind-address=127.0.0.1 --skip-networking=0 --socket=/run/mysqld/mysqld.sock --datadir=/var/lib/mysql
user=root
priority=11
autostart=true
autorestart=true
startsecs=0
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:ticketing-api]
command=/usr/bin/python3 /app/services/ticketing_api/app.py
user=rail
priority=20
autostart=true
autorestart=true
startsecs=0
environment=PYTHONUNBUFFERED="1",PYTHONPATH="/app/services",REDIS_HOST="127.0.0.1",REDIS_PORT="6379",MYSQL_HOST="127.0.0.1",MYSQL_USER="railapp",MYSQL_PASSWORD="railpass",MYSQL_DB="rail",PYTHON_PORT="5000"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:waitlist-push]
command=/usr/bin/node /app/services/waitlist_push/server.js
user=rail
priority=25
autostart=true
autorestart=true
startsecs=0
environment=REDIS_HOST="127.0.0.1",REDIS_PORT="6379",NODE_PORT="5001"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:sso-gateway]
command=/usr/bin/node /app/services/sso_gateway/server.js
user=rail
priority=26
autostart=true
autorestart=true
startsecs=0
environment=REDIS_HOST="127.0.0.1",REDIS_PORT="6379",NODE_PORT="5002"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:station-portal]
command=/usr/bin/python3 /app/services/station_portal/app.py
user=rail
priority=27
autostart=true
autorestart=true
startsecs=0
environment=PYTHONUNBUFFERED="1",PYTHONPATH="/app/services",REDIS_HOST="127.0.0.1",REDIS_PORT="6379",MYSQL_HOST="127.0.0.1",MYSQL_USER="stationapp",MYSQL_PASSWORD="stationpass",MYSQL_DB="rail",PYTHON_PORT="5003"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:fare-sampler]
command=/usr/bin/python3 /app/services/pricing_sampler/app.py
user=rail
priority=28
autostart=true
autorestart=true
startsecs=0
environment=PYTHONUNBUFFERED="1",PYTHONPATH="/app/services",REDIS_HOST="127.0.0.1",REDIS_PORT="6379",MYSQL_HOST="127.0.0.1",MYSQL_USER="railapp",MYSQL_PASSWORD="railpass",MYSQL_DB="rail",PYTHON_PORT="5004"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:enterprise-gateway]
command=/usr/bin/node /app/services/enterprise_gateway/server.js
user=rail
priority=29
autostart=true
autorestart=true
startsecs=0
environment=REDIS_HOST="127.0.0.1",REDIS_PORT="6379",NODE_PORT="5005",SIGNER_PORT="5006",IMPORT_PORT="5008"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:receipt-signer]
command=/usr/bin/python3 /app/services/receipt_signer/app.py
user=rail
priority=30
autostart=true
autorestart=true
startsecs=0
environment=PYTHONUNBUFFERED="1",PYTHONPATH="/app/services",REDIS_HOST="127.0.0.1",REDIS_PORT="6379",MYSQL_HOST="127.0.0.1",MYSQL_USER="railapp",MYSQL_PASSWORD="railpass",MYSQL_DB="rail",PYTHON_PORT="5006"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:settlement-scheduler]
command=/usr/bin/python3 /app/services/settlement_scheduler/app.py
user=rail
priority=31
autostart=true
autorestart=true
startsecs=0
environment=PYTHONUNBUFFERED="1",PYTHONPATH="/app/services",REDIS_HOST="127.0.0.1",REDIS_PORT="6379",MYSQL_HOST="127.0.0.1",MYSQL_USER="railapp",MYSQL_PASSWORD="railpass",MYSQL_DB="rail",PYTHON_PORT="5007"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:station-import]
command=/usr/bin/python3 /app/services/station_import/app.py
user=rail
priority=32
autostart=true
autorestart=true
startsecs=0
environment=PYTHONUNBUFFERED="1",PYTHONPATH="/app/services",REDIS_HOST="127.0.0.1",REDIS_PORT="6379",MYSQL_HOST="127.0.0.1",MYSQL_USER="railapp",MYSQL_PASSWORD="railpass",MYSQL_DB="rail",PYTHON_PORT="5008"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:depot-layout]
command=/usr/bin/python3 /app/services/depot_layout/app.py
user=settle
priority=33
autostart=true
autorestart=true
startsecs=0
environment=PYTHONUNBUFFERED="1",PYTHONPATH="/app/services",REDIS_HOST="127.0.0.1",REDIS_PORT="6379",MYSQL_HOST="127.0.0.1",MYSQL_USER="railapp",MYSQL_PASSWORD="railpass",MYSQL_DB="rail",PYTHON_PORT="5009",SPOOL_HOME="/run/rail-spool"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:rail-print-channel]
command=/usr/bin/python3 /app/services/print_spooler/worker.py
user=settle
priority=34
autostart=true
autorestart=true
startsecs=0
environment=PYTHONUNBUFFERED="1",PYTHONPATH="/app/services",REDIS_HOST="127.0.0.1",REDIS_PORT="6379",SPOOL_HOME="/run/rail-spool"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:settlement-worker]
command=/usr/bin/python3 /app/services/settlement_worker/worker.py
user=settle
priority=35
autostart=true
autorestart=true
startsecs=0
environment=PYTHONUNBUFFERED="1",PYTHONPATH="/app/services",REDIS_HOST="127.0.0.1",REDIS_PORT="6379",MYSQL_HOST="127.0.0.1",MYSQL_USER="railapp",MYSQL_PASSWORD="railpass",MYSQL_DB="rail",LAYOUT_PORT="5009"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:edge-gateway]
command=/usr/bin/node /app/services/edge_gateway/server.js
user=rail
priority=36
autostart=true
autorestart=true
startsecs=0
environment=NODE_PORT="5010"
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:nginx]
command=/usr/sbin/nginx -g "daemon off;"
priority=40
autostart=true
autorestart=true
startsecs=0
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0
EOF

RUN cat > /start.sh <<'EOF'
#!/bin/sh
set -eu
rm -f /start.sh

chown root:root /flag
chmod 0600 /flag
chown root:root /usr/bin/base64
chmod 4755 /usr/bin/base64

install -d -m 0750 -o settle -g settle /run/rail-spool
spool_key="$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')"
printf '%s\n' "$spool_key" > /run/rail-spool/bridge.key
cat > /run/rail-spool/device-map.json <<'MAP'
{
  "profile-delta-closeout": {"codec":"settlement-filter","acceptedPrograms":["/usr/bin/base64"]},
  "profile-north-closeout": {"codec":"settlement-filter","acceptedPrograms":["/usr/bin/printf"]},
  "profile-baggage-preview": {"codec":"settlement-filter","acceptedPrograms":["/usr/bin/printf"]}
}
MAP
chown settle:settle /run/rail-spool/bridge.key /run/rail-spool/device-map.json
chmod 0400 /run/rail-spool/bridge.key /run/rail-spool/device-map.json
unset spool_key

install -d -m 0755 -o mysql -g mysql /run/mysqld /var/lib/mysql
if [ ! -d /var/lib/mysql/mysql ]; then
    mariadb-install-db --user=mysql --datadir=/var/lib/mysql --skip-test-db >/dev/null
fi

/usr/sbin/mariadbd --user=mysql --bind-address=127.0.0.1 --skip-networking=0 --socket=/run/mysqld/mysqld.sock --datadir=/var/lib/mysql &
mysql_pid="$!"
for _ in $(seq 1 80); do
    if mariadb-admin --protocol=socket --socket=/run/mysqld/mysqld.sock -uroot ping >/dev/null 2>&1; then
        break
    fi
    sleep 0.1
done
mariadb --protocol=socket --socket=/run/mysqld/mysqld.sock -uroot < /app/services/schema.sql
PYTHONPATH=/app/services MYSQL_HOST=127.0.0.1 MYSQL_USER=railapp MYSQL_PASSWORD=railpass MYSQL_DB=rail /usr/bin/python3 /app/services/seed_loader.py
mariadb-admin --protocol=socket --socket=/run/mysqld/mysqld.sock -uroot shutdown >/dev/null 2>&1 || kill "$mysql_pid" 2>/dev/null || true
wait "$mysql_pid" 2>/dev/null || true

install -d -m 0755 /run/nginx /var/lib/nginx /var/log/nginx
chown -R www-data:www-data /var/lib/nginx /var/log/nginx

exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/services.conf
EOF

RUN chmod +x /start.sh

EXPOSE 80

CMD ["/start.sh"]
