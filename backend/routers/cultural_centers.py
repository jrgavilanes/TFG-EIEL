from collections import OrderedDict
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import sql

from database import db_dependency_postgres, fetch_records_and_convert
from routers.audit import register_user_access
from routers.auth import user_dependency
from routers.helpers import exists_equipment, release_nomecalles_layer, delete_images_from_s3, recalculate_cod, \
    get_new_code, check_municipaly, get_images, get_all_my_records_by_table_name, \
    update_record_geom_with_nomecalles_geom, update_nomecalles

router = APIRouter(
    prefix='/api/cultural-centers',
    tags=['/api/cultural-centers']
)

EIEL_TABLE_NAME = "cent_cultural"
ORDER_FIELD = "orden_centro"
NOMECALLES_TABLES_NAMES = [
    "parroquias",
    "plazastoros",
    "museos",
    "cines",
    "galerias",
    "centrolectura",
    "librerias",
    "bibliometro",
    "biblimunicipal",
    "bibliobus",
    "teatros"
]
TIPO_EQUIPAMIENTO = "CU"


class CulturalCenterCreateRequest(BaseModel):
    fase: str
    clave: str
    prov: str
    mun: str
    ent: str
    poblamiento: str
    orden_centro: str
    nombre: str
    tipo_centro: Optional[str]
    titular: Optional[str]
    gestion: Optional[str]
    s_cubi: Optional[int]
    s_aire: Optional[int]
    s_sola: Optional[int]
    acceso_s_ruedas: Optional[str]
    estado: Optional[str]
    cod: str
    borrado: str
    field_nomecalles: Optional[str]
    lat: float
    lng: float
    usos: object
    usos_s_cubi: object


class CulturalCenterUpdateRequest(BaseModel):
    gid: int
    nombre: str
    tipo_centro: Optional[str]
    titular: Optional[str]
    gestion: Optional[str]
    s_cubi: Optional[int]
    s_aire: Optional[int]
    s_sola: Optional[int]
    acceso_s_ruedas: Optional[str]
    estado: Optional[str]
    usos: object
    usos_s_cubi: object


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
        delete from eiel.cent_cultural_usos where cent_cultural_gid = :gid;
    """)
    values = {
        "gid": gid
    }
    db_postgres.execute(query, values)

    query = sql.text(f"""
        delete from eiel.cent_cultural
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
        select uso, s_cubi from eiel.cent_cultural_usos where cent_cultural_gid = :gid;
    """)
    values = {
        "gid": gid
    }
    records = fetch_records_and_convert(db_postgres, query, values)
    usos = {}
    usos_s_cubi = {}
    for uso in records:
        usos_s_cubi[uso.get("uso")] = uso.get("s_cubi")
        usos[uso.get("uso")] = True

    query = sql.text(f"""
        select
            gid,
            nombre,
            tipo_centro,
            titular,
            gestion,
            s_cubi,
            s_aire,
            s_sola,
            acceso_s_ruedas,
            estado,
            cod,
            ST_AsGeoJSON(ST_Transform(geom,	4326)) as geom            
        from eiel.cent_cultural 
        where gid = :gid;
    """)
    values = {
        "gid": gid
    }
    record = fetch_records_and_convert(db_postgres, query, values)
    if len(record) > 0:
        record = record[0]
        record["images"] = images
        record["usos_s_cubi"] = usos_s_cubi
        record["usos"] = usos
        return record
    else:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")


@router.put("/{gid}", status_code=204)
async def update_by_gid(
        gid: int,
        equipment: CulturalCenterUpdateRequest,
        db_postgres: db_dependency_postgres,
        user: user_dependency
):
    if gid != equipment.gid:
        raise HTTPException(status_code=400, detail="El gid del equipamiento no coincide con el gid del objeto")

    await exists_equipment(db_postgres, gid, table_name=EIEL_TABLE_NAME)
    await check_municipaly(db_postgres, gid, user, table_name=EIEL_TABLE_NAME)

    query = sql.text(f"""
        update eiel.cent_cultural
        set nombre = :nombre,
            tipo_centro = :tipo_centro,
            titular = :titular,
            gestion = :gestion,
            s_cubi = :s_cubi,
            s_aire = :s_aire,
            s_sola = :s_sola,
            acceso_s_ruedas = :acceso_s_ruedas,
            estado = :estado
        where gid = :gid;
    """)
    values = {
        "gid": gid,
        "nombre": equipment.nombre,
        "tipo_centro": equipment.tipo_centro,
        "titular": equipment.titular,
        "gestion": equipment.gestion,
        "s_cubi": equipment.s_cubi,
        "s_aire": equipment.s_aire,
        "s_sola": equipment.s_sola,
        "acceso_s_ruedas": equipment.acceso_s_ruedas,
        "estado": equipment.estado
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
    return await get_all_my_records_by_table_name(db_postgres, user, EIEL_TABLE_NAME)


@router.post("/", status_code=201)
async def insert_equipment(
        db_postgres: db_dependency_postgres,
        equipment: CulturalCenterCreateRequest,
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
    equipment.orden_centro = result.get("order_field")
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


async def insert_equipment_in_db(equipment, db_postgres):
    query = sql.text(f"""
        SELECT
            COUNT(*) AS num_regs
        FROM eiel.cent_cultural
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
        INSERT INTO eiel.cent_cultural(
            fase, clave, prov, mun, ent, poblamiento, orden_centro, nombre, tipo_centro, titular, gestion, s_cubi, 
            s_aire, s_sola, acceso_s_ruedas, estado, cod, borrado, 
            geom            
        )
        VALUES (
            :fase, :clave, :prov, :mun, :ent, :poblamiento, :orden_centro, :nombre, :tipo_centro, :titular, :gestion,
             :s_cubi, :s_aire, :s_sola, :acceso_s_ruedas, :estado, :cod, :borrado,             
            st_transform(ST_SetSRID(ST_MakePoint(:lng,:lat), 4326),3857
            )
        )
        RETURNING eiel.cent_cultural.gid;
    """)
    values = {
        "fase": equipment.fase,
        "clave": equipment.clave,
        "prov": equipment.prov,
        "mun": equipment.mun,
        "ent": equipment.ent,
        "poblamiento": equipment.poblamiento,
        "orden_centro": equipment.orden_centro,
        "nombre": equipment.nombre,
        "tipo_centro": equipment.tipo_centro,
        "titular": equipment.titular,
        "gestion": equipment.gestion,
        "s_cubi": equipment.s_cubi,
        "s_aire": equipment.s_aire,
        "s_sola": equipment.s_sola,
        "acceso_s_ruedas": equipment.acceso_s_ruedas,
        "estado": equipment.estado,
        "cod": equipment.cod,
        "borrado": equipment.borrado,
        "lng": equipment.lng,
        "lat": equipment.lat
    }
    try:
        result = db_postgres.execute(query, values)
        inserted_id = result.fetchone()[0]
        await update_nomecalles(db_postgres=db_postgres, field_nomecalles=equipment.field_nomecalles)
        await insert_usos_in_db(db_postgres, equipment, inserted_id)
        return {"inserted_id": inserted_id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e.orig))


async def insert_usos_in_db(db_postgres, equipment, cent_cultural_gid):
    for uso_key in equipment.usos.keys():
        query = sql.text(f"""
            INSERT INTO eiel.cent_cultural_usos (
                cent_cultural_gid, cod, fase, clave, prov, mun, ent, poblamiento, orden_centro, uso, s_cubi )
            select gid, cod, fase, clave , prov, mun, ent, poblamiento , orden_centro, :uso, :usos_s_cubi
            from eiel.cent_cultural where gid = :cent_cultural_gid;
        """)
        values = {
            "uso": uso_key,
            "usos_s_cubi": equipment.usos_s_cubi[uso_key],
            "cent_cultural_gid": cent_cultural_gid
        }
        db_postgres.execute(query, values)


async def update_usos_in_db(db_postgres, equipment):
    query = sql.text(f"""
        DELETE FROM eiel.cent_cultural_usos WHERE cent_cultural_gid = :gid;        
    """)
    values = {
        "gid": equipment.gid
    }
    db_postgres.execute(query, values)

    for uso_key in equipment.usos.keys():
        query = sql.text(f"""
            INSERT INTO eiel.cent_cultural_usos (
                cent_cultural_gid, cod, fase, clave, prov, mun, ent, poblamiento, orden_centro, uso, s_cubi)
            select gid, cod, fase, clave , prov, mun, ent, poblamiento , orden_centro, :uso, :s_cubi 
            from eiel.cent_cultural where gid = :cent_cultural_gid;
        """)
        values = {
            "uso": uso_key,
            "s_cubi": equipment.usos_s_cubi[uso_key],
            "cent_cultural_gid": equipment.gid
        }
        db_postgres.execute(query, values)
