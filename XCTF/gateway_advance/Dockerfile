FROM openresty/openresty:alpine

COPY ./nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY ./www /www
RUN echo "L3HCTF{test_flag}" > /flag
RUN echo "test_password" > /password

EXPOSE 24

CMD ["sh", "-c", "openresty -g 'daemon off;'"]