import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.handlers import routers
from app.db import engine, AsyncSessionLocal
from app.models import Base
from app.services.balance_service import BalanceService

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    stop_event = asyncio.Event()

    async def _sweeper_loop():
        while not stop_event.is_set():
            try:
                async with AsyncSessionLocal() as session:
                    async with session.begin():
                        service = BalanceService(session)
                        await service.sweep_expired_transactions()
            except Exception as e:
                print(f"Sweeper error: {e}")
            await asyncio.sleep(5.0)

    task = asyncio.create_task(_sweeper_loop())
    try:
        yield
    finally:
        stop_event.set()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)