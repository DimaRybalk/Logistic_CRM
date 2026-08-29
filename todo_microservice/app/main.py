import uuid

from fastapi import FastAPI, Request
import time

from fastapi.responses import JSONResponse
from app.router import task_router
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(title="To-Do CRM")


app.include_router(task_router.router, prefix="/api/v1")


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
    return {"status": "ok", "service": "todo_microservice"}
