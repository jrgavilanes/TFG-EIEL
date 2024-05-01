import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

POSTGRES_USER = os.getenv('POSTGRES_USER', 'janrax')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'janrax')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'sig_local')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '8003')

POSTGRES_DATABASE_URL = (
    f'postgresql+psycopg2://{POSTGRES_USER}:'
    f'{POSTGRES_PASSWORD}@'
    f'{POSTGRES_HOST}:{POSTGRES_PORT}'
    f'/{POSTGRES_DB}'
)
engine_postgres = create_engine(POSTGRES_DATABASE_URL)

SessionLocalPostgres = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres)


def get_db_postgres():
    db = SessionLocalPostgres()
    try:
        yield db
    finally:
        db.close()


def fetch_records_and_convert(db, query, values=None):
    records = db.execute(query, values)
    return [dict(zip(records.keys(), row)) for row in records.fetchall()]


db_dependency_postgres = Annotated[Session, Depends(get_db_postgres)]
