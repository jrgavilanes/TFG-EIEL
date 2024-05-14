docker start helper_frontend && docker exec helper_frontend sh /build_frontend.sh && docker stop helper_frontend
docker exec -it tfg-eiel_backend_1 pip install -r requirements.txt
docker restart tfg-eiel_backend_1