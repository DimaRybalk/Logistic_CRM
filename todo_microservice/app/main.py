from fastapi import FastAPI, Request
import time
from app.router import task_router
import logging

app = FastAPI(title="To-Do CRM")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


app.include_router(task_router.router, prefix="/api")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    response_time = time.perf_counter() - start_time
    logger.info(
        f"{request.method} {request.url.path} {response.status_code} {response_time:.3f}s"
    )
    return response


@app.get("/")
async def root():
    return {"status": "ok", "service": "todo_microservice"}
