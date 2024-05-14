import json
from collections import OrderedDict
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import sql

from database import db_dependency_postgres, fetch_records_and_convert
from routers.audit import register_user_access
from routers.auth import user_dependency
from routers.helpers import exists_equipment, release_nomecalles_layer, delete_images_from_s3, recalculate_cod, \
    check_municipaly, get_images, get_all_my_records_by_table_name, get_new_code, \
    update_record_geom_with_nomecalles_geom, update_nomecalles

router = APIRouter(
    prefix='/api/landfills',
    tags=['/api/landfills']
)

EIEL_TABLE_NAME = "vertedero"
ORDER_FIELD = "orden_ver"
NOMECALLES_TABLES_NAMES = [
    "puntoslim",
    "peligrosos",
    "vertederos",
]
TIPO_EQUIPAMIENTO = "VT"


class LandfillCreateRequest(BaseModel):
    fase: str
    clave: str
    prov: str
    mun: str
    orden_ver: str
    is_greater_50k: bool
    internal_nombre: str
    tipo_ver: Optional[str]
    titular: Optional[str]
    gestion: Optional[str]
    olores: Optional[str]
    humos: Optional[str]
    cont_anima: Optional[str]
    r_inun: Optional[str]
    filtracion: Optional[str]
    impacto_v: Optional[str]
    frec_averia: Optional[str]
    saturacion: Optional[str]
    inestable: Optional[str]
    otros: Optional[str]
    capac_tot: Optional[int] = None
    capac_tot_porc: Optional[int] = None
    capac_ampl: Optional[str] = None
    capac_transf: Optional[int] = None
    vida_util: Optional[int]
    categoria: Optional[str]
    actividad: Optional[str]
    estado: Optional[str]
    cod: str
    borrado: str
    field_nomecalles: str
    lat: float
    lng: float


class LandfillUpdateRequest(BaseModel):
    gid: int
    internal_nombre: str
    is_greater_50k: bool
    tipo_ver: Optional[str]
    titular: Optional[str]
    gestion: Optional[str]
    olores: Optional[str]
    humos: Optional[str]
    cont_anima: Optional[str]
    r_inun: Optional[str]
    filtracion: Optional[str]
    impacto_v: Optional[str]
    frec_averia: Optional[str]
    saturacion: Optional[str]
    inestable: Optional[str]
    otros: Optional[str]
    capac_tot: Optional[int] = None
    capac_tot_porc: Optional[int] = None
    capac_ampl: Optional[str] = None
    capac_transf: Optional[int] = None
    vida_util: Optional[int]
    categoria: Optional[str]
    actividad: Optional[str]
    estado: Optional[str]


@router.delete("/{gid}", status_code=204)
async def delete_by_gid(
        user: user_dependency,
        gid: int,
        db_postgres: db_dependency_postgres
):
    if user.get("role") not in ["admin", "operator"]:
        raise HTTPException(status_code=402, detail="Acción no permitida para rol ayuntamiento")

    record = await exists_equipment(db_postgres=db_postgres, gid=gid, table_name=EIEL_TABLE_NAME)
    cod = record.get("cod")

    await release_nomecalles_layer(db_postgres, gid, table_name=EIEL_TABLE_NAME,
                                   nomecalles_tables_names=NOMECALLES_TABLES_NAMES)

    query = sql.text(f"""
        delete from eiel.vert_encuestado where vertedero_gid = :gid;
    """)
    values = {
        "gid": gid
    }
    db_postgres.execute(query, values)

    query = sql.text(f"""
        delete from eiel.vert_encuestado_m50 where vertedero_gid = :gid;
    """)
    values = {
        "gid": gid
    }
    db_postgres.execute(query, values)

    query = sql.text(f"""
        delete from eiel.vertedero
        where gid = :gid;
    """)
    values = {
        "gid": gid
    }
    db_postgres.execute(query, values)
    await register_user_access(db_postgres=db_postgres,
                               user_id=user.get("user_id"),
                               equipment=f"eiel.{EIEL_TABLE_NAME}",
                               function_name="delete_by_gid",
                               parameters={"gid": gid})

    await delete_images_from_s3(db_postgres=db_postgres, gid=gid, tipo_equipamiento=TIPO_EQUIPAMIENTO)
    await recalculate_cod(cod=cod, db_postgres=db_postgres, table_name=EIEL_TABLE_NAME, order_field=ORDER_FIELD)
    db_postgres.commit()


# async def release_nomecalles_layer(db_postgres, gid):
#     layers = [
#         "puntoslim",
#         "peligrosos",
#         "vertederos",
#     ]
#
#     for layer in layers:
#         query = sql.text(f"""
#                 update nomecalles.{layer} c set used = 'N'
#                 where ST_DWithin(c.geom, (select geom from eiel.vertedero where gid = :gid), 1)
#             """)
#         values = {
#             "gid": gid
#         }
#         db_postgres.execute(query, values)


@router.get("/{gid}")
async def get_by_gid(
        user: user_dependency,
        gid: int,
        db_postgres: db_dependency_postgres
):
    await exists_equipment(db_postgres, gid, table_name=EIEL_TABLE_NAME)
    await check_municipaly(db_postgres, gid, user, table_name=EIEL_TABLE_NAME)
    images = await get_images(db_postgres=db_postgres, gid=gid, tipo_equipamiento=TIPO_EQUIPAMIENTO)

    query = sql.text(f"""
        select * from eiel.vert_encuestado where vertedero_gid = :gid;
    """)
    values = {
        "gid": gid
    }
    vertedero_menos_50k = fetch_records_and_convert(db_postgres, query, values)

    query = sql.text(f"""
            select * from eiel.vert_encuestado_m50 where vertedero_gid = :gid;
        """)
    values = {
        "gid": gid
    }

    vertedero_mas_50k = fetch_records_and_convert(db_postgres, query, values)

    is_greater_50k = True if len(vertedero_mas_50k) > 0 else False
    if is_greater_50k:
        vertedero_detail = vertedero_mas_50k
    else:
        vertedero_detail = vertedero_menos_50k

    query = sql.text(f"""
        select
            gid,
            fase,
            clave,
            prov,
            mun,
            internal_nombre as nombre,
            cod,
            ST_AsGeoJSON(ST_Transform(geom,	4326)) as geom            
        from eiel.vertedero 
        where gid = :gid;
    """)
    values = {
        "gid": gid
    }
    record = fetch_records_and_convert(db_postgres, query, values)

    if len(record) > 0:
        record = record[0]
        record["is_greater_50k"] = is_greater_50k
        record["detail"] = vertedero_detail
        record["images"] = images
        return record
    else:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")


@router.put("/{gid}", status_code=204)
async def update_by_gid(
        user: user_dependency,
        gid: int,
        equipment: LandfillUpdateRequest,
        db_postgres: db_dependency_postgres
):
    if gid != equipment.gid:
        raise HTTPException(status_code=400, detail="El gid del equipamiento no coincide con el gid del objeto")

    await exists_equipment(db_postgres, gid, table_name=EIEL_TABLE_NAME)
    await check_municipaly(db_postgres, gid, user, table_name=EIEL_TABLE_NAME)

    query = sql.text(f"""
        update eiel.vertedero
        set internal_nombre = :internal_nombre
        where gid = :gid;
    """)
    values = {
        "internal_nombre": equipment.internal_nombre,
        "gid": gid
    }
    try:
        db_postgres.execute(query, values)
        await update_usos_in_db(db_postgres, equipment)
        await register_user_access(db_postgres=db_postgres,
                                   user_id=user.get("user_id"),
                                   equipment=f"eiel.{EIEL_TABLE_NAME}",
                                   function_name="update_by_gid",
                                   parameters=equipment.model_dump())
        db_postgres.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e.orig))


@router.get("/")
async def get_all(
        db_postgres: db_dependency_postgres,
        user: user_dependency
):
    ORDER_FIELD = {
        "vertedero": "orden_ver",
    }
    table_name = 'vertedero'
    if user.get("role") not in ["cityhall"]:
        query = sql.text(f"""
            select
                v.gid as gid, 
                '{table_name}' as tabla,
                v.{ORDER_FIELD.get(table_name)} as orden,
                COALESCE(ve.completo, false) AS completo,
                concat('(',v.{ORDER_FIELD.get(table_name)},') ', internal_nombre) as mi_etiqueta,
                ST_AsGeoJSON(ST_Transform(v.geom, 4326)) AS geom  
            from eiel.vertedero v left join (
                select * from eiel.vert_encuestado
                union
                select * from eiel.vert_encuestado_m50
            ) ve on v.gid = ve.vertedero_gid;
        """)
        equipments = fetch_records_and_convert(db_postgres, query)
    else:
        query = sql.text(f"""
            select
                v.gid as gid, 
                '{table_name}' as tabla,
                v.{ORDER_FIELD.get(table_name)} as orden,
                COALESCE(ve.completo, false) AS completo,
                concat('(',v.{ORDER_FIELD.get(table_name)},') ', internal_nombre) as mi_etiqueta,
                ST_AsGeoJSON(ST_Transform(v.geom, 4326)) AS geom  
            from eiel.vertedero v left join (
                select * from eiel.vert_encuestado
                union
                select * from eiel.vert_encuestado_m50
            ) ve on v.gid = ve.vertedero_gid
            where mun = :mun;
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


@router.post("/", status_code=201)
async def insert_equipment(
        db_postgres: db_dependency_postgres,
        equipment: LandfillCreateRequest,
        user: user_dependency,
):
    if user.get("role") not in ["admin", "operator"]:
        raise HTTPException(status_code=402, detail="Rol ayuntamiento no puede insertar equipamientos")

    await recalculate_cod(db_postgres=db_postgres,
                          cod=equipment.cod,
                          table_name=EIEL_TABLE_NAME,
                          order_field=ORDER_FIELD)

    result = await get_new_code(db_postgres=db_postgres, cod=equipment.cod, table_name=EIEL_TABLE_NAME)
    equipment.cod = result.get("new_cod")
    equipment.orden_ver = result.get("order_field")
    gid = await insert_equipment_in_db(equipment, db_postgres)
    parameters = OrderedDict()
    parameters["gid"] = gid.get("inserted_id")
    parameters.update(equipment.model_dump())

    await register_user_access(db_postgres=db_postgres,
                               user_id=user.get("user_id"),
                               equipment=f"eiel.{EIEL_TABLE_NAME}",
                               function_name="insert_equipment",
                               parameters=parameters)

    await update_record_geom_with_nomecalles_geom(
        db_postgres=db_postgres,
        eiel_table_name=EIEL_TABLE_NAME,
        eiel_gid=gid.get("inserted_id"),
        field_nomecalles=equipment.field_nomecalles
    )

    db_postgres.commit()
    return gid


# async def recalculate_cod(cod, db_postgres):
#     query = sql.text(f"""
#         SELECT
#             COUNT(*) AS num_regs,
#             RIGHT(MAX(cod), 3)::int AS last_code,
#             CASE
#                 WHEN COUNT(*) = 0 AND RIGHT(MAX(cod), 3)::int IS NULL THEN 'YES'
#                 WHEN COUNT(*) = RIGHT(MAX(cod), 3)::int THEN 'YES'
#                 ELSE 'NO'
#             END AS is_correct
#         FROM eiel.vertedero
#         where cod like :cod
#     """)
#     values = {
#         "cod": f"{cod}%"
#     }
#     record = fetch_records_and_convert(db_postgres, query, values)
#     record = record[0]
#     is_correct = record.get("is_correct")
#     if is_correct == "NO":
#         query = sql.text(f"""
#             select gid
#             from eiel.vertedero c
#             where cod like :cod
#             order by gid asc;
#         """)
#         values = {
#             "cod": f"{cod}%"
#         }
#         records = fetch_records_and_convert(db_postgres, query, values)
#         for i, record in enumerate(records):
#             query = sql.text(f"""
#                 update eiel.vertedero
#                 set cod = :new_cod, orden_ver = :orden_ver
#                 where gid = :gid;
#             """)
#             values = {
#                 "new_cod": f"{cod}{str(i + 1).zfill(3)}",
#                 "orden_ver": f"{str(i + 1).zfill(3)}",
#                 "gid": record.get("gid")
#             }
#             db_postgres.execute(query, values)
#             db_postgres.commit()


async def insert_equipment_in_db(equipment, db_postgres):
    query = sql.text(f"""
        SELECT
            COUNT(*) AS num_regs
        FROM eiel.vertedero
        WHERE ST_Equals(geom, st_transform(ST_SetSRID(ST_MakePoint(:lng,:lat), 4326),3857));
    """)
    values = {
        "lng": equipment.lng,
        "lat": equipment.lat
    }
    record = fetch_records_and_convert(db_postgres, query, values)
    record = record[0]
    num_regs = record.get("num_regs")
    if num_regs > 0:
        raise HTTPException(status_code=400, detail="La coordenada ya existe en la tabla del equipamiento")

    query = sql.text(f"""
        INSERT INTO eiel.vertedero(
            fase, clave, prov, mun, orden_ver, internal_nombre, cod, 
            geom            
        )
        VALUES (
            :fase, :clave, :prov, :mun, :orden_ver, :internal_nombre, :cod,             
            st_transform(ST_SetSRID(ST_MakePoint(:lng,:lat), 4326),3857
            )
        )
        RETURNING eiel.vertedero.gid;
    """)
    values = {
        "fase": equipment.fase,
        "clave": equipment.clave,
        "prov": equipment.prov,
        "mun": equipment.mun,
        "orden_ver": equipment.orden_ver,
        "internal_nombre": equipment.internal_nombre,
        "cod": equipment.cod,
        "lng": equipment.lng,
        "lat": equipment.lat
    }
    try:
        result = db_postgres.execute(query, values)
        # db_postgres.commit()
        inserted_id = result.fetchone()[0]
        await update_nomecalles(db_postgres=db_postgres, field_nomecalles=equipment.field_nomecalles)
        await insert_usos_in_db(db_postgres, equipment, inserted_id)
        return {"inserted_id": inserted_id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e.orig))


async def insert_usos_in_db(db_postgres, equipment, vertedero_gid):
    query = sql.text(f"""
        DELETE FROM eiel.vert_encuestado WHERE vertedero_gid = :vertedero_gid;
    """)
    values = {
        "vertedero_gid": vertedero_gid
    }
    db_postgres.execute(query, values)

    query = sql.text(f"""
        DELETE FROM eiel.vert_encuestado_m50 WHERE vertedero_gid = :vertedero_gid;
    """)
    values = {
        "vertedero_gid": vertedero_gid
    }
    db_postgres.execute(query, values)

    tabla = "vert_encuestado"
    if equipment.is_greater_50k:
        tabla = "vert_encuestado_m50"

    query = sql.text(f"""
        INSERT INTO eiel.{tabla} (
            tipo_ver, titular, gestion, olores, humos, 
            cont_anima, r_inun, filtracion, impacto_v, frec_averia, saturacion, inestable, otros, capac_tot,
            capac_tot_porc, capac_ampl, capac_transf, estado, vida_util, categoria, actividad, vertedero_gid 
        )
        VALUES(
            :tipo_ver, :titular, :gestion, :olores, :humos, 
            :cont_anima, :r_inun, :filtracion, :impacto_v, :frec_averia, :saturacion, :inestable, :otros, :capac_tot,
            :capac_tot_porc, :capac_ampl, :capac_transf, :estado, :vida_util, :categoria, :actividad, :vertedero_gid
        );
    """)
    values = {
        "tipo_ver": equipment.tipo_ver,
        "titular": equipment.titular,
        "gestion": equipment.gestion,
        "olores": equipment.olores,
        "humos": equipment.humos,
        "cont_anima": equipment.cont_anima,
        "r_inun": equipment.r_inun,
        "filtracion": equipment.filtracion,
        "impacto_v": equipment.impacto_v,
        "frec_averia": equipment.frec_averia,
        "saturacion": equipment.saturacion,
        "inestable": equipment.inestable,
        "otros": equipment.otros,
        "capac_tot": equipment.capac_tot,
        "capac_tot_porc": equipment.capac_tot_porc,
        "capac_ampl": equipment.capac_ampl,
        "capac_transf": equipment.capac_transf,
        "estado": equipment.estado,
        "vida_util": equipment.vida_util,
        "categoria": equipment.categoria,
        "actividad": equipment.actividad,
        "vertedero_gid": vertedero_gid
    }

    db_postgres.execute(query, values)
    # db_postgres.commit()


async def update_usos_in_db(db_postgres, equipment):
    await insert_usos_in_db(db_postgres, equipment, equipment.gid)

# async def update_nomecalles(equipment, db_postgres):
#     if equipment.field_nomecalles:
#         try:
#             tabla = equipment.field_nomecalles.split("|")[0]
#             gid = equipment.field_nomecalles.split("|")[1]
#             query = sql.text(f"""
#                 UPDATE nomecalles.{tabla} SET used = 'S' WHERE gid = :gid;
#             """)
#             values = {
#                 "gid": gid
#             }
#             db_postgres.execute(query, values)
#             db_postgres.commit()
#         except Exception as e:
#             print(e)
#
#
# async def get_new_code(equipment, db_postgres):
#     query = sql.text(f"""
#             SELECT max(cod) AS last_cod from eiel.vertedero
#             WHERE cod like :cod
#         """)
#     values = {
#         "cod": f"{equipment.cod}%"
#     }
#     last_cod = fetch_records_and_convert(db_postgres, query, values)
#     if len(last_cod) > 0:
#         last_cod = last_cod[0].get("last_cod")
#         if last_cod is not None:
#             last_cod = last_cod[-3:]
#             last_cod = int(last_cod) + 1
#             last_cod = str(last_cod).zfill(3)
#             equipment.cod = f"{equipment.cod}{last_cod}"
#             equipment.orden_ver = last_cod
#         else:
#             equipment.cod = f"{equipment.cod}001"
#             equipment.orden_ver = "001"
#     else:
#         equipment.cod = f"{equipment.cod}001"
#         equipment.orden_ver = "001"
