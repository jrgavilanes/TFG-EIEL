import json
import os
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import sql
from starlette import status
from starlette.requests import Request
from user_agents import parse

from database import db_dependency_postgres, fetch_records_and_convert

router = APIRouter(
    prefix='/api/auth',
    tags=['/api/auth']
)

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY',
                           "d1fc798b7e37a3e3fdfe42773aa449ba523b2139f52c09809eaf12a98b37de93")  # $ openssl rand -hex 32
ALGORITHM = 'HS256'
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, ALGORITHM)
        username: str = payload.get("username")
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        municipality: str = payload.get("municipality")
        is_desktop: bool = payload.get("is_desktop")
        if username is None or user_id is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="No autorizado - Token inválido o caducado")
        return {
            "username": username,
            "user_id": user_id,
            "role": role,
            "municipality": municipality,
            "is_desktop": is_desktop
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="No autorizado - Token inválido o caducado")


user_dependency = Annotated[dict, Depends(get_current_user)]


class CreateUserRequest(BaseModel):
    name: str
    password: str
    role: str
    municipality: Optional[str]


@router.post("/", status_code=201)
async def create_user(
        db_postgres: db_dependency_postgres,
        user_request: CreateUserRequest,
        user: user_dependency,
):
    if user.get("role") != "admin":
        raise HTTPException(status_code=402, detail="No eres Rol admin. Acción no permitida")

    query = sql.text(f"""
        insert into auth.users (name, password, role, municipality) 
        values (:name, :password, :role, :municipality) 
        returning id;
    """)
    values = {
        "name": user_request.name,
        "password": bcrypt_context.hash(user_request.password),
        "role": user_request.role,
        "municipality": user_request.municipality
    }
    try:
        user_id = fetch_records_and_convert(db_postgres, query, values)
        db_postgres.commit()
        return {"id": user_id[0].get("id")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e.orig))


class ValidateUserRequest(BaseModel):
    name: str
    password: str


@router.post("/validate", status_code=200)
async def validate_user(
        request: Request,
        db_postgres: db_dependency_postgres,
        user_request: ValidateUserRequest,
):
    user_agent_str = request.headers.get("User-Agent", "")
    user_agent = parse(user_agent_str)

    query = sql.text(f"""
        select id, name, role, municipality, password 
        from auth.users 
        where name = :name and active = true;
    """)
    values = {
        "name": user_request.name,
    }
    user = fetch_records_and_convert(db_postgres, query, values)
    if len(user) == 0:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    user = user[0]
    if not bcrypt_context.verify(user_request.password, user.get("password")):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    return await create_access_token(username=user.get("name"), user_id=user.get("id"), role=user.get("role"),
                                     municipality=user.get("municipality"), is_desktop=user_agent.is_pc,
                                     expires_delta=timedelta(hours=8))


async def create_access_token(username: str, user_id: int, role: str, municipality: str, is_desktop: bool,
                              expires_delta: timedelta):
    expires = datetime.utcnow() + expires_delta
    encode = {
        "username": username,
        "id": str(user_id),
        "role": role,
        "municipality": municipality,
        "is_desktop": is_desktop,
        "exp": expires
    }
    return jwt.encode(encode, key=JWT_SECRET_KEY, algorithm=ALGORITHM)


@router.get("/users", status_code=200)
async def get_users(
        db_postgres: db_dependency_postgres,
        user: user_dependency
):
    query = sql.text(f"""
        select id, name, role, municipality
        from auth.users
        where id = :user_id;
    """)
    values = {
        "user_id": user.get("user_id")
    }
    users = fetch_records_and_convert(db_postgres, query, values)
    return users
