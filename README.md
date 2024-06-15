# TFG EIEL

## Entorno de desarrollo

Copia y configura .env ```cp .env-template .env```

Construye entorno ```docker-compose -f docker-compose-dev.yml up --build```

## Entorno de producción

Copia y configura .env ```cp .env-template .env```

Construye entorno ```docker-compose up --build```

Restaura base de datos (Elimina la base de datos, crea base datos, restaura backup completo )
```bash
# Detiene todos los contenedores activos y levanta sólo la base de datos
docker-compose -f docker-compose.yml stop && docker start tfg-postgis-eiel

docker exec tfg-postgis-eiel dropdb -U janrax sig_local && docker exec tfg-postgis-eiel createdb -U janrax sig_local
docker exec -i tfg-postgis-eiel psql -U janrax -d sig_local < backup_base.sql
```



