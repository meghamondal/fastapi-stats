from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid

EMAIL = "23f1000744@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://dash-u7pnij.example.com"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
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

@app.post("/verify")
async def verify(data: dict = Body(...)):
    return {"valid": False}