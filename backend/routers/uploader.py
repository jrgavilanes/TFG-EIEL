import io
import os
from datetime import datetime

import boto3
import uuid
from PIL import Image, ImageOps
from botocore.config import Config
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import sql

from database import db_dependency_postgres, fetch_records_and_convert
from routers.audit import register_user_access
from routers.auth import user_dependency

router = APIRouter(
    prefix='/api/upload',
    tags=['/api/upload']
)

TABLE_NAME = 'eiel.equipamiento_fotos'

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', "")
S3_REGION_NAME = os.getenv('S3_REGION_NAME', "")
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', "")
S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID', "")
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY', "")
S3_PHOTO_BASE_URL = os.getenv('S3_PHOTO_BASE_URL', "")
S3_PHOTO_MINIFY_BASE_URL = os.getenv('S3_PHOTO_MINIFY_BASE_URL', "")


class UploadUpdateRequest(BaseModel):
    idef: str
    tipo: str
    comentario: str


@router.delete("/{idef}", status_code=204)
async def delete_file(
        user: user_dependency,
        db_postgres: db_dependency_postgres,
        idef: str
):
    if user.get("role") not in ["admin", "operator"]:
        raise HTTPException(status_code=402, detail="acción no permitida")

    await register_user_access(db_postgres=db_postgres,
                               user_id=user.get("user_id"),
                               equipment=TABLE_NAME,
                               function_name="delete_file",
                               parameters={"idef": idef})

    query = sql.text("""
        SELECT idef,original_path, minify_path
        FROM eiel.equipamiento_fotos
        WHERE idef = :idef
    """)
    values = {
        "idef": idef
    }
    result = fetch_records_and_convert(db_postgres, query, values)
    if len(result) > 0:
        original_path = result[0].get("original_path")
        minify_path = result[0].get("minify_path")
        delete_from_bucket(S3_BUCKET_NAME, original_path.split(f'{S3_PHOTO_BASE_URL}/')[1])
        delete_from_bucket(S3_BUCKET_NAME, minify_path.split(f'{S3_PHOTO_BASE_URL}/')[1])
        query = sql.text("""
            DELETE FROM eiel.equipamiento_fotos
            WHERE idef = :idef
        """)
        values = {
            "idef": idef
        }
        db_postgres.execute(query, values)
        db_postgres.commit()


@router.put("/{idef}", status_code=204)
async def update_file(
        db_postgres: db_dependency_postgres,
        idef: str,
        request: UploadUpdateRequest,
        user: user_dependency,
):
    if user.get("role") not in ["admin", "operator"]:
        raise HTTPException(status_code=402, detail="acción no permitida")

    await register_user_access(db_postgres=db_postgres,
                               user_id=user.get("user_id"),
                               equipment=TABLE_NAME,
                               function_name="update_file",
                               parameters=request.model_dump())

    query = sql.text("""
        UPDATE eiel.equipamiento_fotos
        SET tipo = :tipo, comentario = :comentario
        WHERE idef = :idef
    """)
    values = {
        "idef": idef,
        "tipo": request.tipo,
        "comentario": request.comentario
    }
    db_postgres.execute(query, values)
    db_postgres.commit()


@router.post("/{equipment_type}/{gid}/{cod}/{lat}/{lng}", status_code=200)
async def upload_file(
        background_tasks: BackgroundTasks,
        db_postgres: db_dependency_postgres,
        user: user_dependency,
        equipment_type: str,
        gid: int,
        cod: str,
        lat: float,
        lng: float,
        new_file: UploadFile = File(...),

):
    if user.get("role") not in ["admin", "operator"]:
        raise HTTPException(status_code=402, detail="acción no permitida")

    file_contents = await new_file.read()
    filename = str(uuid.uuid4())
    extension = os.path.splitext(new_file.filename)[1]

    background_tasks.add_task(upload_to_bucket, file_contents, S3_BUCKET_NAME, f'{filename}{extension}',
                              new_file.content_type)

    background_tasks.add_task(minify_image_and_upload, file_contents, S3_BUCKET_NAME,
                              f"{S3_PHOTO_MINIFY_BASE_URL.split('/')[-1]}/{filename}{extension}",
                              new_file.content_type)

    query = sql.text("""
        INSERT INTO eiel.equipamiento_fotos (idef, tipo_equipamiento, tipo_equipamiento_gid, original_path, minify_path, fecha_hora, lat, lng, cod) 
        VALUES (:idef,:tipo_equipamiento, :tipo_equipamiento_gid, :original_path, :minify_path, :fecha_hora, :lat, :lng, :cod)
        """)
    values = {
        "idef": filename,
        "tipo_equipamiento": equipment_type,
        "tipo_equipamiento_gid": gid,
        "original_path": f'{S3_PHOTO_BASE_URL}/{filename}{extension}',
        "minify_path": f'{S3_PHOTO_MINIFY_BASE_URL}/{filename}{extension}',
        "fecha_hora": datetime.now().strftime("%Y%m%d%H%M%S"),
        "lat": lat,
        "lng": lng,
        "cod": cod
    }
    db_postgres.execute(query, values)

    await register_user_access(db_postgres=db_postgres,
                               user_id=user.get("user_id"),
                               equipment=TABLE_NAME,
                               function_name="upload_file",
                               parameters={"equipment_type": equipment_type,
                                           "gid": gid,
                                           "cod": cod,
                                           "idef": filename,
                                           "lat": lat,
                                           "lng": lng
                                           }
                               )

    db_postgres.commit()

    return {
        "equipment_type": equipment_type,
        "idef": filename,
        "filename": f'{S3_PHOTO_MINIFY_BASE_URL}/{filename}{extension}',
    }


def minify_image_and_upload(file_contents, bucket_name, object_name, content_type):
    # Create a file-like object from the file contents
    file = io.BytesIO(file_contents)

    # Map MIME types to image formats
    format_map = {
        'image/jpeg': 'JPEG',
        'image/jpg': 'JPEG',
        'image/png': 'PNG',
        'image/gif': 'GIF',
        # Add more mappings if needed
    }

    if content_type not in format_map:
        print(f'Unsupported file type: {content_type}')
        return

    img_format = format_map[content_type]

    # Open the image file
    with Image.open(file) as img:
        # Correct the orientation of the image based on its EXIF data
        img = ImageOps.exif_transpose(img)

        original_width, original_height = img.size
        new_width = int(original_width * 0.15)  # 15% of the original width
        new_height = int(original_height * 0.15)  # 15% of the original height
        img_resized = img.resize((new_width, new_height), resample=Image.LANCZOS)

        output = io.BytesIO()
        img_resized.save(output, format=img_format)
        output.seek(0)

    upload_to_bucket(output.read(), bucket_name, object_name, content_type)


def upload_to_bucket(file_contents, bucket_name, object_name, content_type):
    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=S3_REGION_NAME,
                            endpoint_url=S3_ENDPOINT_URL,
                            aws_access_key_id=S3_ACCESS_KEY_ID,
                            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
                            config=Config(signature_version='s3v4'))

    # create a file-like object from the file contents
    file = io.BytesIO(file_contents)

    client.upload_fileobj(Fileobj=file,
                          Bucket=bucket_name,
                          Key=object_name,
                          ExtraArgs={'ACL': 'public-read', 'ContentType': content_type})


def delete_from_bucket(bucket_name, object_name):
    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=S3_REGION_NAME,
                            endpoint_url=S3_ENDPOINT_URL,
                            aws_access_key_id=S3_ACCESS_KEY_ID,
                            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
                            config=Config(signature_version='s3v4'))

    client.delete_object(Bucket=bucket_name, Key=object_name)
