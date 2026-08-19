from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.database import connect_db, close_db
from app.api.upload import router as upload_router
from app.api.retrive import router as retrival_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    
    yield
    
    await close_db()

app = FastAPI(
    title="Finex backend",
    lifespan=lifespan
)

app.include_router(upload_router)
app.include_router(retrival_router)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "backend"}


# @app.get("/health")
# def health_check():
#     return {"status": "healthy"}
