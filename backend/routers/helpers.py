import json
from collections import OrderedDict

from fastapi import APIRouter, HTTPException
from sqlalchemy import sql

from database import db_dependency_postgres, fetch_records_and_convert
from routers.audit import register_user_access
from routers.auth import user_dependency
from routers.uploader import delete_from_bucket, S3_BUCKET_NAME, S3_PHOTO_BASE_URL

router = APIRouter(
    prefix='/api/helpers',
    tags=['/api/helpers']
)


@router.get("/info")
async def get_info_by_lng_lat(
        db_postgres: db_dependency_postgres,
        lng: float = -3.9256235449773556,
        lat: float = 40.29790055130107
):
    return await info_by_lng_lat(db_postgres, lat, lng)


async def info_by_lng_lat(db_postgres, lat, lng):
    fase = "2023"
    entidad_colectiva = "00"
    provincia = "28"
    entidad = ""
    municipio = ""
    poblamiento = "99"
    query = sql.text(f"""
        select codine, geocodigo 
        from nomecalles.nucleos 
        where ST_INTERSECTS(geom, st_transform(ST_SetSRID(ST_MakePoint(:lng,:lat), 4326),3857));
    """)
    values = {
        "lng": lng,
        "lat": lat
    }
    nucleo = fetch_records_and_convert(db_postgres, query, values)
    if len(nucleo) > 0:
        poblamiento = nucleo[0].get("geocodigo")
        poblamiento = poblamiento[-2:]
    query = sql.text(f"""
        select geocodigo 
        from nomecalles.entidades 
        where ST_INTERSECTS(geom, st_transform(ST_SetSRID(ST_MakePoint(:lng,:lat), 4326),3857));
    """)
    values = {
        "lng": lng,
        "lat": lat
    }
    qentidad = fetch_records_and_convert(db_postgres, query, values)
    if len(qentidad) > 0:
        geocodigo = qentidad[0].get("geocodigo")
        entidad = f"00{geocodigo[-2:]}"
        municipio = geocodigo[:3]

    return {
        "lng": lng,
        "lat": lat,
        "fase": fase,
        "provincia": provincia,
        "entidad_colectiva": entidad_colectiva,
        "entidad": entidad,
        "municipio": municipio,
        "poblamiento": poblamiento,
        "qnucleo": nucleo,
        "qentidad": qentidad,
    }


@router.get("/info_by_geom")
async def get_info_by_geom(
        db_postgres: db_dependency_postgres,
        geom: str = "0101000020110F0000553DF21085C117C1C0095F0B6EE35241"
):
    fase = "2023"
    entidad_colectiva = "00"
    provincia = "28"
    entidad = ""
    municipio = ""
    poblamiento = "99"

    query = sql.text(f"""
        select 
            st_x(st_transform('{geom}'::geometry,4326)) as lng, 
            st_y(st_transform('{geom}'::geometry,4326)) as lat;
    """)
    coords = fetch_records_and_convert(db_postgres, query)
    coords = coords[0]
    lng = coords.get("lng")
    lat = coords.get("lat")

    query = sql.text(f"""
        select codine, geocodigo 
        from nomecalles.nucleos 
        where ST_INTERSECTS(geom, :geom);
    """)

    values = {
        "geom": geom
    }

    nucleo = fetch_records_and_convert(db_postgres, query, values)

    if len(nucleo) > 0:
        poblamiento = nucleo[0].get("geocodigo")
        poblamiento = poblamiento[-2:]

    query = sql.text(f"""
        select geocodigo 
        from nomecalles.entidades 
        where ST_INTERSECTS(geom, :geom);
    """)

    values = {
        "geom": geom
    }

    qentidad = fetch_records_and_convert(db_postgres, query, values)

    if len(qentidad) > 0:
        geocodigo = qentidad[0].get("geocodigo")
        entidad = f"00{geocodigo[-2:]}"
        municipio = geocodigo[:3]

    return {
        "lng": lng,
        "lat": lat,
        "fase": fase,
        "provincia": provincia,
        "entidad_colectiva": entidad_colectiva,
        "entidad": entidad,
        "municipio": municipio,
        "poblamiento": poblamiento,
        "qnucleo": nucleo,
        "qentidad": qentidad,
    }


@router.put("/move/{gid}/{table}", status_code=204)
async def move_geom(
        user: user_dependency,
        db_postgres: db_dependency_postgres,
        gid: int,
        table: str,
        lat: float,
        lng: float,
):
    if user.get("role") not in ["admin", "operator"]:
        raise HTTPException(status_code=402, detail="Acción no permitida para rol ayuntamiento")

    new_coord = await info_by_lng_lat(db_postgres, lat, lng)
    if table == "vertedero":
        query = sql.text(f"""
               select mun as municipio 
               from eiel.{table}        
               where gid = :gid;
           """)
    else:
        query = sql.text(f"""
               select mun as municipio, poblamiento 
               from eiel.{table}        
               where gid = :gid;
           """)

    values = {
        "gid": gid
    }
    record = fetch_records_and_convert(db_postgres, query, values)
    if len(record) > 0:
        record = record[0]
        if table == "vertedero":
            if record["municipio"] == new_coord.get("municipio"):
                query = sql.text(f"""
                    update eiel.{table}
                    set geom = st_transform(ST_SetSRID(ST_MakePoint(:lng,:lat), 4326),3857)
                    where gid = :gid;
                """)
                values = {
                    "gid": gid,
                    "lng": lng,
                    "lat": lat
                }
                db_postgres.execute(query, values)

                parameters = OrderedDict()
                parameters["gid"] = gid
                parameters["table"] = table
                parameters["new_lat"] = lat
                parameters["new_lng"] = lng

                await register_user_access(db_postgres=db_postgres,
                                           user_id=user.get("user_id"),
                                           equipment=f"eiel.{table}",
                                           function_name="move_geom",
                                           parameters=parameters)

                db_postgres.commit()
                return
            else:
                raise HTTPException(status_code=400,
                                    detail="Diferente municipio. No se puede mover el equipamiento a esa localización")
        else:
            if record["municipio"] == new_coord.get("municipio") and record["poblamiento"] == new_coord.get(
                    "poblamiento"):
                query = sql.text(f"""
                    update eiel.{table}
                    set geom = st_transform(ST_SetSRID(ST_MakePoint(:lng,:lat), 4326),3857)
                    where gid = :gid;
                """)
                values = {
                    "gid": gid,
                    "lng": lng,
                    "lat": lat
                }
                db_postgres.execute(query, values)
                parameters = OrderedDict()
                parameters["gid"] = gid
                parameters["table"] = table
                parameters["new_lat"] = lat
                parameters["new_lng"] = lng

                await register_user_access(db_postgres=db_postgres,
                                           user_id=user.get("user_id"),
                                           equipment=f"eiel.{table}",
                                           function_name="move_geom",
                                           parameters=parameters)
                db_postgres.commit()
                return
            else:
                raise HTTPException(status_code=400,
                                    detail="Diferente municipio y poblamiento. No se puede mover el equipamiento a esa localización")

    raise HTTPException(status_code=404, detail="No se ha encontrado el equipamiento")


async def exists_equipment(db_postgres: db_dependency_postgres, gid: int, table_name: str):
    query = sql.text(f"""
        select gid, cod 
        from eiel.{table_name} 
        where gid = :gid;
    """)
    values = {
        "gid": gid
    }
    record = fetch_records_and_convert(db_postgres, query, values)
    if len(record) == 0:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")

    return record[0]


async def check_municipaly(db_postgres: db_dependency_postgres, gid: int, user: user_dependency, table_name: str):
    if user.get("role") in ["cityhall"]:
        query = sql.text(f"""
                select gid                    
                from eiel.{table_name} 
                where gid = :gid and mun = :mun;
            """)
        values = {
            "gid": gid,
            "mun": user.get("municipality")
        }
        record = fetch_records_and_convert(db_postgres, query, values)
        if len(record) == 0:
            raise HTTPException(status_code=402, detail="Equipamiento no pertence a su municipio")


async def delete_images_from_s3(db_postgres: db_dependency_postgres, gid: int, tipo_equipamiento: str):
    # Delete images from bucket and database
    query = sql.text(f"""
        select * 
        from eiel.equipamiento_fotos ef 
        where tipo_equipamiento_gid = :gid and tipo_equipamiento = :tipo_equipamiento
    """)
    values = {
        "gid": gid,
        "tipo_equipamiento": tipo_equipamiento
    }
    images = fetch_records_and_convert(db_postgres, query, values)
    for image in images:
        delete_from_bucket(S3_BUCKET_NAME, image.get("original_path").split(f'{S3_PHOTO_BASE_URL}/')[1])
        delete_from_bucket(S3_BUCKET_NAME, image.get("minify_path").split(f'{S3_PHOTO_BASE_URL}/')[1])
    query = sql.text(f"""
        delete from eiel.equipamiento_fotos
        where tipo_equipamiento_gid = :gid and tipo_equipamiento = :tipo_equipamiento
    """)
    values = {
        "gid": gid,
        "tipo_equipamiento": tipo_equipamiento
    }
    db_postgres.execute(query, values)


async def release_nomecalles_layer(db_postgres: db_dependency_postgres,
                                   gid: int,
                                   table_name: str,
                                   nomecalles_tables_names: list):
    for nomecalles_table_name in nomecalles_tables_names:
        query = sql.text(f"""
           update nomecalles.{nomecalles_table_name} c set used = 'N' 
           where c.geom = (select geom from eiel.{table_name} where gid = :gid)
        """)
        values = {
            "gid": gid
        }
        db_postgres.execute(query, values)


async def recalculate_cod(db_postgres: db_dependency_postgres, cod: str, table_name: str, order_field: str):
    query = sql.text(f"""
        SELECT 
            COUNT(*) AS num_regs,
            RIGHT(MAX(cod), 3)::int AS last_code,
            CASE 
                WHEN COUNT(*) = 0 AND RIGHT(MAX(cod), 3)::int IS NULL THEN 'YES'
                WHEN COUNT(*) = RIGHT(MAX(cod), 3)::int THEN 'YES'
                ELSE 'NO'
            END AS is_correct
        FROM eiel.{table_name}
        where cod like :cod
    """)
    values = {
        "cod": f"{cod[:13]}%"
    }
    record = fetch_records_and_convert(db_postgres, query, values)
    record = record[0]
    is_correct = record.get("is_correct")
    if is_correct == "NO":
        query = sql.text(f"""
            select gid 
            from eiel.{table_name} 
            where cod like :cod 
            order by gid asc;
        """)
        values = {
            "cod": f"{cod[:13]}%"
        }
        records = fetch_records_and_convert(db_postgres, query, values)
        for i, record in enumerate(records):
            query = sql.text(f"""
                update eiel.{table_name}
                set cod = :new_cod, {order_field} = :order_field
                where gid = :gid;
            """)
            values = {
                "new_cod": f"{cod[:13]}{str(i + 1).zfill(3)}",
                "order_field": f"{str(i + 1).zfill(3)}",
                "gid": record.get("gid")
            }
            db_postgres.execute(query, values)


async def get_images(db_postgres: db_dependency_postgres, gid: int, tipo_equipamiento: str):
    query = sql.text(f"""
        select * 
        from eiel.equipamiento_fotos ef 
        where tipo_equipamiento_gid = :gid and tipo_equipamiento = :tipo_equipamiento;
    """)
    values = {
        "gid": gid,
        "tipo_equipamiento": tipo_equipamiento
    }
    images = fetch_records_and_convert(db_postgres, query, values)
    return images


async def get_new_code(db_postgres: db_dependency_postgres,
                       cod: str,
                       table_name: str):
    response = {
        "new_cod": "",
        "order_field": ""
    }
    query = sql.text(f"""
            SELECT max(cod) AS last_cod from eiel.{table_name}
            WHERE cod like :cod            
        """)
    values = {
        "cod": f"{cod[:13]}%"
    }
    last_cod = fetch_records_and_convert(db_postgres, query, values)
    if len(last_cod) > 0:
        last_cod = last_cod[0].get("last_cod")
        if last_cod is not None:
            last_cod = last_cod[-3:] if len(last_cod) == 16 else "000"
            last_cod = int(last_cod) + 1
            last_cod = str(last_cod).zfill(3)
            response["new_cod"] = f"{cod[:13]}{last_cod}"
            response["order_field"] = last_cod
            return response
        else:
            response["new_cod"] = f"{cod[:13]}001"
            response["order_field"] = "001"
            return response
    else:
        response["new_cod"] = f"{cod[:13]}001"
        response["order_field"] = "001"
        return response


async def update_nomecalles(db_postgres: db_dependency_postgres, field_nomecalles: str):
    if field_nomecalles:
        try:
            tabla = field_nomecalles.split("|")[0]
            gid = field_nomecalles.split("|")[1]
            query = sql.text(f"""
                UPDATE nomecalles.{tabla} SET used = 'S' WHERE gid = :gid;            
            """)
            values = {
                "gid": gid
            }
            db_postgres.execute(query, values)
        except Exception as e:
            # No es un equipamiento de nomecalles
            pass


async def update_record_geom_with_nomecalles_geom(db_postgres: db_dependency_postgres,
                                                  eiel_table_name: str,
                                                  eiel_gid: int,
                                                  field_nomecalles: str):
    if field_nomecalles:
        try:
            tabla = field_nomecalles.split("|")[0]
            gid = field_nomecalles.split("|")[1]
            query = sql.text(f"""
                update eiel.{eiel_table_name} c 
                set geom = (select cc.geom 
                            from nomecalles.{tabla} cc 
                            where cc.gid = :gid) 
                where c.gid = :eiel_gid;            
            """)
            values = {
                "gid": gid,
                "eiel_gid": eiel_gid
            }
            db_postgres.execute(query, values)
        except Exception as e:
            # No es un equipamiento de nomecalles
            pass


async def get_all_my_records_by_table_name(
        db_postgres: db_dependency_postgres,
        user: user_dependency,
        table_name: str
):
    ORDER_FIELD = {
        "cementerio": "orden_cement",
        "casa_consistorial": "orden_casa",
        "centro_asistencial": "orden_casis",
        "centro_ensenanza": "orden_cent",
        "centro_sanitario": "orden_csan",
        "cent_cultural": "orden_centro",
        "edific_pub_sin_uso": "orden_edific",
        "instal_deportiva": "orden_instal",
        "lonja_merc_feria": "orden_lmf",
        "matadero": "orden_matad",
        "parque": "orden_parq",
        "tanatorio": "orden_tanat",
        "proteccion_civil": "orden_prot",
        "vertedero": "orden_ver",
    }
    if user.get("role") not in ["cityhall"]:
        query = sql.text(f"""
            select 
                gid, 
                '{table_name}' as tabla,
                {ORDER_FIELD.get(table_name)} as orden,
                completo,
                concat('(',{ORDER_FIELD.get(table_name)},') ', nombre) as mi_etiqueta, 
                ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geom 
            from eiel.{table_name};
        """)
        equipments = fetch_records_and_convert(db_postgres, query)
    else:
        query = sql.text(f"""
            select 
                gid, 
                '{table_name}' as tabla, 
                {ORDER_FIELD.get(table_name)} as orden,
                completo,
                concat('(',{ORDER_FIELD.get(table_name)},') ', nombre) as mi_etiqueta, 
                ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geom 
            from eiel.{table_name} where mun = :mun;
        """)
        values = {
            "mun": user.get("municipality")
        }
        equipments = fetch_records_and_convert(db_postgres, query, values)
    if len(equipments) > 0:
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": json.loads(feature["geom"]),
                    "properties": {
                        "gid": feature["gid"],
                        "tabla": feature["tabla"],
                        "orden": feature["orden"],
                        "completo": feature["completo"],
                        "mi_etiqueta": feature["mi_etiqueta"],
                        "geom": feature["geom"]
                    }
                }
                for feature in equipments
            ]
        }
        return geojson
    else:
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        return geojson
