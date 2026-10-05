import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import init_db
from .routes import router
from .worker import worker_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    stop_event = asyncio.Event()
    worker_task = asyncio.create_task(worker_loop(stop_event))

    app.state.worker_stop_event = stop_event
    app.state.worker_task = worker_task

    yield

    stop_event.set()
    await worker_task


app = FastAPI(
    title="Webhook Delivery Engine",
    version="1.0.0",
    description="Webhook ingestion, delivery, retries, attempt history, and HMAC signing.",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
