# Utiliza la imagen base de PHP con Apache
FROM php:7.4-apache

# Habilita el módulo mod_rewrite de Apache
RUN a2enmod rewrite

# Configura la zona horaria a Europe/Madrid
RUN echo "Europe/Madrid" > /etc/timezone && ln -sf /usr/share/zoneinfo/Europe/Madrid /etc/localtime
