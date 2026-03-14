#!/bin/bash
# Initial SSL certificate setup with Let's Encrypt
# Run once on the server to obtain the first certificate

set -euo pipefail

DOMAIN="${1:-chartora.com}"
EMAIL="${2:-admin@chartora.com}"

echo "[$(date -Iseconds)] Setting up SSL certificate for $DOMAIN..."

# Create webroot directory
mkdir -p /var/www/certbot

# Obtain certificate
certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

echo "[$(date -Iseconds)] SSL certificate obtained for $DOMAIN"
echo "Certificate location: /etc/letsencrypt/live/$DOMAIN/"
echo ""
echo "Now restart nginx: docker compose -f infra/docker-compose.prod.yml restart nginx"
