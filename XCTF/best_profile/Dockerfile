FROM openresty/openresty:alpine

COPY ./nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY docker-entrypoint.sh /
COPY ./app /app

WORKDIR /app
RUN apk add --no-cache python3 py3-flask py3-flask-sqlalchemy py3-flask-login py3-requests py3-geoip2
RUN echo L3HCTF{test_flag} > /flag

EXPOSE 80

ENTRYPOINT [ "/docker-entrypoint.sh" ]