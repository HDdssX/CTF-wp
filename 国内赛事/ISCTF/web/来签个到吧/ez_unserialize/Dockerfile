FROM php:8.2-apache

WORKDIR /var/www/html
COPY src/ /var/www/html/
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x -R /app
RUN apt-get update && apt-get install -y libsqlite3-dev vim-common &&\
    rm -rf /var/lib/apt/lists/*
RUN docker-php-ext-install pdo pdo_sqlite

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["apache2-foreground"]



