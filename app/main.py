from contextlib import asynccontextmanager
from os import sync
from typing import AsyncGenerator
from fastapi import FastAPI, Depends, status, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

@asynccontextmanager
async def lifespan(app: FastAPI):
    database = Database(DATABASE_URL)
    engine = create_async_engine(DATABASE_URL, echo=True)

    fabrica_sesiones = async_sessionmaker(bind=engine, expire_on_commit=False)

    app.state.engine = engine
    app.state.fabrica_sesiones = fabrica_sesiones

    yield

    await database.disconnect()

app = FastAPI(lifespan=lifespan)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with app.state.fabrica_sesiones() as session:
        yield session

@app.get("/health/live", status_code=200)
async def health_live():
    return {"estado": "okey"}

@app.get("/health/ready")
async def health_ready(response: Response, session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1"))
        
        return {"estado": "okey"}
    except Exception as e:
            response.status_code = 503
            return {"estado": "error", "detalle": str(e)}