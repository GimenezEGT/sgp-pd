#!/bin/sh
# Gera certificado autoassinado SOMENTE se nenhum certificado foi montado em /etc/nginx/certs.
# Em homologação e produção, monte o certificado emitido pela CA interna da empresa.
set -eu
CERT_DIR=/etc/nginx/certs
CN="${SGP_CERT_CN:-localhost}"
if [ ! -s "$CERT_DIR/sgp.crt" ] || [ ! -s "$CERT_DIR/sgp.key" ]; then
    echo "[sgp] nenhum certificado montado: gerando certificado autoassinado de desenvolvimento para $CN"
    mkdir -p "$CERT_DIR"
    openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
        -subj "/CN=$CN" \
        -addext "subjectAltName=DNS:$CN,IP:127.0.0.1" \
        -keyout "$CERT_DIR/sgp.key" -out "$CERT_DIR/sgp.crt" >/dev/null 2>&1
fi
