from collections import OrderedDict
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import sql

from database import db_dependency_postgres, fetch_records_and_convert
from routers.audit import register_user_access
from routers.auth import user_dependency
from routers.helpers import exists_equipment, update_record_geom_with_nomecalles_geom, release_nomecalles_layer, \
    delete_images_from_s3, recalculate_cod, get_images, check_municipaly, get_all_my_records_by_table_name, \
    get_new_code, update_nomecalles

router = APIRouter(
    prefix='/api/cemeteries',
    tags=['/api/cemeteries']
)

EIEL_TABLE_NAME = "cementerio"
ORDER_FIELD = "orden_cement"
NOMECALLES_TABLES_NAMES = [
    "cementerios"
]
TIPO_EQUIPAMIENTO = "CE"


class CemeteryCreateRequest(BaseModel):
    fase: str
    clave: str
    prov: str
    mun: str
    ent: str
    poblamiento: str
    orden_cement: str
    nombre: Optional[str]
    titular: Optional[str]
    distancia: Optional[float]
    acceso: Optional[str]
    capilla: Optional[str]
    deposito: Optional[str]
    ampliacion: Optional[str]
    saturacion: Optional[float]
    superficie: Optional[float]
    acceso_s_ruedas: Optional[str]
    crematorio: Optional[str]
    cod: Optional[str]
    borrado: Optional[str]
    field_nomecalles: Optional[str]
    lat: float
    lng: float


class CemeteryUpdateRequest(BaseModel):
    gid: int
    nombre: Optional[str]
    titular: Optional[str]
    distancia: Optional[float]
    acceso: Optional[str]
    capilla: Optional[str]
    deposito: Optional[str]
    ampliacion: Optional[str]
    saturacion: Optional[float]
    superficie: Optional[float]
    acceso_s_ruedas: Optional[str]
    crematorio: Optional[str]


@router.delete("/{gid}", status_code=204)
async def delete_by_gid(
        user: user_dependency,
        gid: int,
        db_postgres: db_dependency_postgres
):
    if user.get("role") not in ["admin", "operator"]:
        raise HTTPException(status_code=402, detail="acción no permitida")

    record = await exists_equipment(db_postgres=db_postgres, gid=gid, table_name=EIEL_TABLE_NAME)

    cod = record.get("cod")

    await release_nomecalles_layer(db_postgres, gid, table_name=EIEL_TABLE_NAME,
                                   nomecalles_tables_names=NOMECALLES_TABLES_NAMES)

    query = sql.text(f"""
        delete from eiel.cementerio
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
        select
            gid,
            nombre,
            titular,
            distancia,
            acceso,
            capilla,
            deposito,
            ampliacion,
            saturacion,
            superficie,
            acceso_s_ruedas,
            crematorio,
            cod,
            ST_AsGeoJSON(ST_Transform(geom,	4326)) as geom
        from eiel.cementerio 
        where gid = :gid;
    """)
    values = {
        "gid": gid
    }
    record = fetch_records_and_convert(db_postgres, query, values)
    if len(record) > 0:
        record = record[0]
        record["images"] = images
        return record
    else:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")


@router.put("/{gid}", status_code=204)
async def update_by_gid(
        user: user_dependency,
        gid: int,
        equipment: CemeteryUpdateRequest,
        db_postgres: db_dependency_postgres
):
    if gid != equipment.gid:
        raise HTTPException(status_code=400, detail="El gid del equipamiento no coincide con el gid del objeto")

    await exists_equipment(db_postgres, gid, table_name=EIEL_TABLE_NAME)
    await check_municipaly(db_postgres, gid, user, table_name=EIEL_TABLE_NAME)

    query = sql.text(f"""
        update eiel.cementerio
        set nombre = :nombre,
            titular = :titular,
            distancia = :distancia,
            acceso = :acceso,
            capilla = :capilla,
            deposito = :deposito,
            ampliacion = :ampliacion,
            saturacion = :saturacion,
            superficie = :superficie,
            acceso_s_ruedas = :acceso_s_ruedas,
            crematorio = :crematorio
        where gid = :gid;
    """)
    values = {
        "gid": gid,
        "nombre": equipment.nombre,
        "titular": equipment.titular,
        "distancia": equipment.distancia,
        "acceso": equipment.acceso,
        "capilla": equipment.capilla,
        "deposito": equipment.deposito,
        "ampliacion": equipment.ampliacion,
        "saturacion": equipment.saturacion,
        "superficie": equipment.superficie,
        "acceso_s_ruedas": equipment.acceso_s_ruedas,
        "crematorio": equipment.crematorio
    }
    try:
        db_postgres.execute(query, values)
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
        user: user_dependency,
):
    return await get_all_my_records_by_table_name(db_postgres, user, EIEL_TABLE_NAME)


@router.post("/", status_code=201)
async def insert_equipment(
        db_postgres: db_dependency_postgres,
        equipment: CemeteryCreateRequest,
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
    equipment.orden_cement = result.get("order_field")
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
        FROM eiel.cementerio
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
        INSERT INTO eiel.cementerio(
            fase, clave, prov, mun, ent, poblamiento, orden_cement, nombre, titular, distancia, acceso, capilla, 
            deposito, ampliacion, saturacion, superficie, acceso_s_ruedas, crematorio, cod, borrado, geom
        )
        VALUES (
            :fase, :clave, :prov, :mun, :ent, :poblamiento, :orden_cement, :nombre, :titular, :distancia, :acceso, 
            :capilla, :deposito, :ampliacion, :saturacion, :superficie, :acceso_s_ruedas, :crematorio, :cod, :borrado, 
            st_transform(ST_SetSRID(ST_MakePoint(:lng,:lat), 4326),3857)
        )
        RETURNING eiel.cementerio.gid;
    """)
    values = {
        "fase": equipment.fase,
        "clave": equipment.clave,
        "prov": equipment.prov,
        "mun": equipment.mun,
        "ent": equipment.ent,
        "poblamiento": equipment.poblamiento,
        "orden_cement": equipment.orden_cement,
        "nombre": equipment.nombre,
        "titular": equipment.titular,
        "distancia": equipment.distancia,
        "acceso": equipment.acceso,
        "capilla": equipment.capilla,
        "deposito": equipment.deposito,
        "ampliacion": equipment.ampliacion,
        "saturacion": equipment.saturacion,
        "superficie": equipment.superficie,
        "acceso_s_ruedas": equipment.acceso_s_ruedas,
        "crematorio": equipment.crematorio,
        "cod": equipment.cod,
        "borrado": equipment.borrado,
        "lng": equipment.lng,
        "lat": equipment.lat
    }
    try:
        result = db_postgres.execute(query, values)
        inserted_id = result.fetchone()[0]
        await update_nomecalles(db_postgres=db_postgres, field_nomecalles=equipment.field_nomecalles)
        return {"inserted_id": inserted_id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e.orig))
