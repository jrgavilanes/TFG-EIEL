from collections import OrderedDict
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import sql

from database import db_dependency_postgres, fetch_records_and_convert
from routers.audit import register_user_access
from routers.auth import user_dependency
from routers.helpers import exists_equipment, release_nomecalles_layer, delete_images_from_s3, recalculate_cod, \
    check_municipaly, get_images, get_all_my_records_by_table_name, update_record_geom_with_nomecalles_geom, \
    get_new_code, update_nomecalles

router = APIRouter(
    prefix='/api/civil-protections',
    tags=['/api/civil-protections']
)

EIEL_TABLE_NAME = "proteccion_civil"
ORDER_FIELD = "orden_prot"
NOMECALLES_TABLES_NAMES = [
    "bomberos",
    "proteccioncivil",
]
TIPO_EQUIPAMIENTO = "IP"


class CivilProtectionCreateRequest(BaseModel):
    fase: str
    clave: str
    prov: str
    mun: str
    ent: str
    poblamiento: str
    orden_prot: str
    nombre: str
    tipo_pciv: Optional[str]
    titular: Optional[str]
    gestion: Optional[str]
    ambito: Optional[str]
    plan_profe: Optional[int]
    plan_volun: Optional[int]
    s_cubi: Optional[int]
    s_aire: Optional[int]
    s_sola: Optional[int]
    acceso_s_ruedas: Optional[str]
    estado: Optional[str]
    vehic_incendio: Optional[int]
    vehic_rescate: Optional[int]
    ambulancia: Optional[int]
    medios_aereos: Optional[int]
    otros_vehi: Optional[int]
    quitanieve: Optional[int]
    detec_ince: Optional[int]
    otros: Optional[int]
    cod: str
    borrado: str
    field_nomecalles: str
    lat: float
    lng: float


class CivilProtectionUpdateRequest(BaseModel):
    gid: int
    nombre: str
    tipo_pciv: Optional[str]
    titular: Optional[str]
    gestion: Optional[str]
    ambito: Optional[str]
    plan_profe: Optional[str]
    plan_volun: Optional[str]
    s_cubi: Optional[str]
    s_aire: Optional[str]
    s_sola: Optional[str]
    acceso_s_ruedas: Optional[str]
    estado: Optional[str]
    vehic_incendio: Optional[str]
    vehic_rescate: Optional[str]
    ambulancia: Optional[str]
    medios_aereos: Optional[str]
    otros_vehi: Optional[str]
    quitanieve: Optional[str]
    detec_ince: Optional[str]
    otros: Optional[str]


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
        delete from eiel.proteccion_civil
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
            tipo_pciv,
            titular,
            gestion,
            ambito,
            plan_profe,
            plan_volun,
            s_cubi,
            s_aire,
            s_sola,
            acceso_s_ruedas,
            estado,
            vehic_incendio,
            vehic_rescate,
            ambulancia,
            medios_aereos,
            otros_vehi,
            quitanieve,
            detec_ince,
            otros,
            cod,
            ST_AsGeoJSON(ST_Transform(geom,	4326)) as geom
        from eiel.proteccion_civil
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
        equipment: CivilProtectionUpdateRequest,
        db_postgres: db_dependency_postgres
):
    if gid != equipment.gid:
        raise HTTPException(status_code=400, detail="El gid del equipamiento no coincide con el gid del objeto")

    await exists_equipment(db_postgres, gid, table_name=EIEL_TABLE_NAME)
    await check_municipaly(db_postgres, gid, user, table_name=EIEL_TABLE_NAME)

    query = sql.text(f"""
        update eiel.proteccion_civil
        set    
            nombre = :nombre,
            tipo_pciv = :tipo_pciv,                        
            titular = :titular,
            gestion = :gestion,
            ambito = :ambito,
            plan_profe = :plan_profe,
            plan_volun = :plan_volun,            
            s_cubi = :s_cubi,
            s_aire = :s_aire,
            s_sola = :s_sola,            
            acceso_s_ruedas = :acceso_s_ruedas,
            estado = :estado,
            vehic_incendio = :vehic_incendio,
            vehic_rescate = :vehic_rescate,
            ambulancia = :ambulancia,
            medios_aereos = :medios_aereos,
            otros_vehi = :otros_vehi,
            quitanieve = :quitanieve,
            detec_ince = :detec_ince,
            otros = :otros
        where gid = :gid;
    """)
    values = {
        "nombre": equipment.nombre,
        "tipo_pciv": equipment.tipo_pciv,
        "titular": equipment.titular,
        "gestion": equipment.gestion,
        "ambito": equipment.ambito,
        "plan_profe": equipment.plan_profe,
        "plan_volun": equipment.plan_volun,
        "s_cubi": equipment.s_cubi,
        "s_aire": equipment.s_aire,
        "s_sola": equipment.s_sola,
        "acceso_s_ruedas": equipment.acceso_s_ruedas,
        "estado": equipment.estado,
        "vehic_incendio": equipment.vehic_incendio,
        "vehic_rescate": equipment.vehic_rescate,
        "ambulancia": equipment.ambulancia,
        "medios_aereos": equipment.medios_aereos,
        "otros_vehi": equipment.otros_vehi,
        "quitanieve": equipment.quitanieve,
        "detec_ince": equipment.detec_ince,
        "otros": equipment.otros,
        "gid": gid,
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
        user: user_dependency,
        db_postgres: db_dependency_postgres
):
    return await get_all_my_records_by_table_name(db_postgres, user, EIEL_TABLE_NAME)


@router.post("/", status_code=201)
async def insert_equipment(
        user: user_dependency,
        db_postgres: db_dependency_postgres,
        equipment: CivilProtectionCreateRequest
):
    if user.get("role") not in ["admin", "operator"]:
        raise HTTPException(status_code=402, detail="Rol ayuntamiento no puede insertar equipamientos")

    await recalculate_cod(db_postgres=db_postgres,
                          cod=equipment.cod,
                          table_name=EIEL_TABLE_NAME,
                          order_field=ORDER_FIELD)

    result = await get_new_code(db_postgres=db_postgres, cod=equipment.cod, table_name=EIEL_TABLE_NAME)
    equipment.cod = result.get("new_cod")
    equipment.orden_prot = result.get("order_field")
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
        FROM eiel.proteccion_civil
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
        INSERT INTO eiel.proteccion_civil (
            fase, clave, prov, mun, ent, poblamiento, orden_prot, nombre, tipo_pciv, titular, gestion,  
            ambito, plan_profe, plan_volun, s_cubi, s_aire, s_sola, acceso_s_ruedas, estado,
            vehic_incendio, vehic_rescate, ambulancia, medios_aereos, otros_vehi, quitanieve, detec_ince, otros,
            cod, borrado, 
            geom            
        )
        VALUES (
            :fase, :clave, :prov, :mun, :ent, :poblamiento, :orden_prot, :nombre, :tipo_pciv, :titular, :gestion,
            :ambito, :plan_profe, :plan_volun, :s_cubi, :s_aire,:s_sola, :acceso_s_ruedas, :estado,
            :vehic_incendio, :vehic_rescate, :ambulancia, :medios_aereos, :otros_vehi, :quitanieve, :detec_ince, :otros, 
            :cod, :borrado,             
            st_transform(ST_SetSRID(ST_MakePoint(:lng,:lat), 4326),3857
            )
        )
        RETURNING eiel.proteccion_civil.gid
    """)
    values = {
        "fase": equipment.fase,
        "clave": equipment.clave,
        "prov": equipment.prov,
        "mun": equipment.mun,
        "ent": equipment.ent,
        "poblamiento": equipment.poblamiento,
        "orden_prot": equipment.orden_prot,
        "nombre": equipment.nombre,
        "tipo_pciv": equipment.tipo_pciv,
        "titular": equipment.titular,
        "gestion": equipment.gestion,
        "ambito": equipment.ambito,
        "plan_profe": equipment.plan_profe,
        "plan_volun": equipment.plan_volun,
        "s_cubi": equipment.s_cubi,
        "s_aire": equipment.s_aire,
        "s_sola": equipment.s_sola,
        "acceso_s_ruedas": equipment.acceso_s_ruedas,
        "estado": equipment.estado,
        "vehic_incendio": equipment.vehic_incendio,
        "vehic_rescate": equipment.vehic_rescate,
        "ambulancia": equipment.ambulancia,
        "medios_aereos": equipment.medios_aereos,
        "otros_vehi": equipment.otros_vehi,
        "quitanieve": equipment.quitanieve,
        "detec_ince": equipment.detec_ince,
        "otros": equipment.otros,
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
