# TFG EIEL

## Entorno de desarrollo

Copia y configura .env ```cp .env-template .env```

Construye entorno ```docker-compose -f docker-compose-dev.yml up --build```

## Entorno de producción

Copia y configura .env ```cp .env-template .env```

Construye entorno ```docker-compose up --build```

Restaura base de datos (Elimina la base de datos, crea base datos, restaura backup completo )
```bash
docker exec postgis-eiel dropdb -U janrax sig_local && docker exec postgis-eiel createdb -U janrax sig_local
docker exec -i postgis-eiel psql -U janrax -d sig_local < db_backup.sql
```



