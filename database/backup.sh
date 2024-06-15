echo "Backup de la base de datos..."
docker exec tfg-postgis-eiel pg_dump -U janrax -d sig_local | gzip > db_backup_$(date +%Y%m%d%H%M%S).sql.gz
echo "Backup y compresión de la base de datos finalizado."