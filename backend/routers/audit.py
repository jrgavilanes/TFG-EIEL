from sqlalchemy import sql
from datetime import datetime
import json


async def register_user_access(db_postgres, user_id, equipment, function_name, parameters, commit=False):
    query = sql.text(f"""
        INSERT INTO auth.audits (user_id, access_time, equipment, function_name, parameters)
        VALUES (:user_id, :access_time, :equipment, :function_name, :parameters)
    """)
    values = {
        "user_id": user_id,
        "access_time": datetime.now(),
        "equipment": equipment,
        "function_name": function_name,
        "parameters": json.dumps(parameters)
    }
    db_postgres.execute(query, values)
    if commit:
        db_postgres.commit()
