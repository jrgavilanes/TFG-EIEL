import os
import uvicorn
from fastapi import FastAPI

from routers import auth, helpers, uploader, cemeteries, assistance_centers

PRODUCTION = os.getenv('PRODUCTION', "false")
if PRODUCTION.lower().strip() == "true":
    app = FastAPI(debug=False, docs_url=None, redoc_url=None)
else:
    app = FastAPI(debug=True, docs_url="/api/docs", openapi_url="/api/openapi.json")

app.include_router(auth.router)
app.include_router(helpers.router)
app.include_router(uploader.router)
app.include_router(cemeteries.router)
app.include_router(assistance_centers.router)


@app.get("/api/")
async def is_live():
    return {"status": "OK"}


if __name__ == '__main__':
    uvicorn.run(app, port=7000, host="127.0.0.1")
