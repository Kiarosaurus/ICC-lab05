#!/bin/bash
# Aprovisionamiento de la instancia EC2 (Ubuntu). Se ejecuta una sola vez,
# en el primer arranque, vía cloud-init. Log: /var/log/cloud-init-output.log
set -eux

export DEBIAN_FRONTEND=noninteractive

# 1. Instalar Docker y el plugin de Docker Compose desde los repos de Ubuntu
apt-get update -y
apt-get install -y docker.io docker-compose-v2
systemctl enable --now docker

# 2. docker-compose de PRODUCCIÓN: usa la imagen publicada en Docker Hub
#    (no hace build local) y levanta también PostgreSQL con volumen.
mkdir -p /opt/mundial
cat > /opt/mundial/docker-compose.yml <<'EOF'
services:
  db:
    image: postgres:15
    container_name: mundial-db
    environment:
      POSTGRES_USER: mundial
      POSTGRES_PASSWORD: mundial123
      POSTGRES_DB: mundial
    volumes:
      - datos_postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mundial -d mundial"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped

  web:
    image: kiarosaurus/mundial-web:latest
    container_name: mundial-web
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: mundial
      DB_USER: mundial
      DB_PASSWORD: mundial123
    ports:
      - "80:8000"     # navegador sin puerto: http://IP
      - "8000:8000"   # puerto directo de la app: http://IP:8000
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  datos_postgres:
EOF

# 3. Descargar las imágenes y levantar la aplicación
cd /opt/mundial
docker compose pull
docker compose up -d
