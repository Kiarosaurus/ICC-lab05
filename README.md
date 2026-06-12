# ⚽ PrediMundial — Lab05 Contenedores

Aplicación de predicciones del Mundial de Fútbol con **arquitectura de 3
capas** (FastAPI + PostgreSQL 15), dockerizada y desplegada en AWS EC2.

## Documentación

- **[INFORME.md](INFORME.md)** — informe del laboratorio con diagramas y evidencias.

## Ejecución rápida

```bash
cp .env.example .env          # opcional: el compose trae estos defaults
docker compose up -d --build
```

Abrir <http://localhost:8000>.

## Despliegue en AWS (Academy)

```bash
docker tag s12lab-web:latest kiarosaurus/mundial-web:latest
docker push kiarosaurus/mundial-web:latest
./deploy_aws.sh               # VPC default + SG + EC2 con user_data.sh
```

Imagen pública: [`kiarosaurus/mundial-web:latest`](https://hub.docker.com/r/kiarosaurus/mundial-web)
