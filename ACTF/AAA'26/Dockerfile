FROM node:26-bookworm

ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0
ENV MONGO_URL=mongodb://127.0.0.1:27017

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg imagemagick ghostscript poppler-utils; \
    curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg; \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" > /etc/apt/sources.list.d/mongodb-org-8.0.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends mongodb-org-server; \
    sed -i 's/domain="coder" rights="none" pattern="PDF"/domain="coder" rights="read" pattern="PDF"/' /etc/ImageMagick-6/policy.xml; \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash app

WORKDIR /app
COPY paper-submission-system/package*.json ./
RUN npm i --omit=dev
COPY paper-submission-system ./
COPY --chmod=444 --chown=root:root flag /flag

RUN set -eux; \
    install -d -m 0755 /data/db /var/log/mongodb /app/public/uploads; \
    chown -R app:app /app; \
    cat > /start.sh <<'EOF'
#!/bin/sh
set -eu

mongod \
  --dbpath /data/db \
  --bind_ip 127.0.0.1 \
  --port 27017 \
  --fork \
  --logpath /var/log/mongodb/mongod.log

for i in $(seq 1 100); do
  if node -e "const net=require('net'); const s=net.connect(27017,'127.0.0.1'); s.on('connect',()=>process.exit(0)); s.on('error',()=>process.exit(1)); setTimeout(()=>process.exit(1),100);" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

cd /app
exec runuser -u app -- env \
  NODE_ENV="${NODE_ENV:-production}" \
  PORT="${PORT:-3000}" \
  HOST="${HOST:-0.0.0.0}" \
  MONGO_URL="${MONGO_URL:-mongodb://127.0.0.1:27017}" \
  node app.js
EOF
RUN chmod +x /start.sh

EXPOSE 3000

ENTRYPOINT ["/start.sh"]
