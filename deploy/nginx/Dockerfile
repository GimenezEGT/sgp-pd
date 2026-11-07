FROM nginx:1.28-alpine
RUN apk add --no-cache openssl
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY 10-certificado-dev.sh /docker-entrypoint.d/10-certificado-dev.sh
RUN chmod +x /docker-entrypoint.d/10-certificado-dev.sh
