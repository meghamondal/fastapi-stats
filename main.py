from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid

import os
import yaml
from dotenv import dotenv_values
from typing import List

EMAIL = "23f1000744@ds.study.iitm.ac.in"
API_KEY = "ak_0trrb6pag42fgfef75nj032v"
ALLOWED_ORIGINS = [
    "https://dash-u7pnij.example.com",
    "https://exam.sanand.workers.dev",
]

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_headers(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response

def to_bool(value):
    return str(value).lower() in ("true", "1", "yes", "on")


def convert_value(key, value):
    if key in ("port", "workers"):
        return int(value)
    elif key == "debug":
        return to_bool(value)
    else:
        return str(value)

@app.get("/stats")
def stats(values: str = Query(...)):
    nums = [int(x) for x in values.split(",")]

    total = sum(nums)

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": total,
        "min": min(nums),
        "max": max(nums),
        "mean": total / len(nums)
    }

from fastapi import Body
import jwt
from fastapi.responses import JSONResponse

ISSUER = "https://idp.exam.local"

AUDIENCE = "tds-s3is6th5.apps.exam.local"

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

@app.post("/verify")
async def verify(data: dict = Body(...)):
    token = data.get("token")

    if not token:
        return JSONResponse(
            status_code=401,
            content={"valid": False},
        )

    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud"),
        }

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"valid": False},
        )
    
from fastapi import Query

@app.get("/effective-config")
def effective_config(set: List[str] = Query(default=[])):
    # 1. Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # 2. YAML
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml") as f:
            yaml_config = yaml.safe_load(f) or {}
        config.update(yaml_config)

    # 3. .env
    env_config = dotenv_values(".env")

    env_map = {
        "APP_API_KEY": "api_key",
        "NUM_WORKERS": "workers"
    }

    for env_key, cfg_key in env_map.items():
        value = env_config.get(env_key)
        if value is not None:
            config[cfg_key] = convert_value(cfg_key, value)

    # 4. OS Environment
    os_map = {
        "APP_PORT": "port",
        "APP_DEBUG": "debug",
        "APP_API_KEY": "api_key",
        "APP_LOG_LEVEL": "log_level",
        "APP_WORKERS": "workers"
    }

    for env_key, cfg_key in os_map.items():
        value = os.environ.get(env_key)
        if value is not None:
            config[cfg_key] = convert_value(cfg_key, value)

    # 5. CLI overrides
    for item in set:
        if "=" in item:
            key, value = item.split("=", 1)
            config[key] = convert_value(key, value)

    # Secret masking
    config["api_key"] = "****"

    return config

from fastapi import Header, HTTPException

@app.post("/analytics")
async def analytics(
    data: dict = Body(...),
    x_api_key: str = Header(None)
):
    # Authentication
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    events = data.get("events", [])

    total_events = len(events)

    unique_users = len(set(event["user"] for event in events))

    revenue = sum(
        event["amount"]
        for event in events
        if event["amount"] > 0
    )

    totals = {}

    for event in events:
        if event["amount"] > 0:
            totals[event["user"]] = (
                totals.get(event["user"], 0)
                + event["amount"]
            )

    top_user = max(totals, key=totals.get) if totals else ""

    return {
        "email": EMAIL,
        "total_events": total_events,
        "unique_users": unique_users,
        "revenue": revenue,
        "top_user": top_user,
    }