import uuid

from fastapi import FastAPI, Request
import time

from fastapi.responses import JSONResponse
from app.router import auth_router, user_router, company_router
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger("app.middleware")

app = FastAPI(title="Auth Microservice")

app.include_router(auth_router.router, prefix="/api/v1", tags=["Auth"])
app.include_router(user_router.router, prefix="/api/v1", tags=["Users"])
app.include_router(company_router.router, prefix="/api/v1", tags=["Companies"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        process_time_ms = (time.perf_counter() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({process_time_ms:.2f}ms)"
        )
        return response

    except Exception as exc:
        process_time_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(
            f"[{request_id}] {request.method} {request.url.path} "
            f"FAILED with error: {exc} ({process_time_ms:.2f}ms)"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={"X-Request-ID": request_id},
        )


@app.get("/")
async def root():
    return {"service": "auth_microservice", "status": "running"}
