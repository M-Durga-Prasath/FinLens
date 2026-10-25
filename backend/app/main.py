import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from app.db.database import connect_db, close_db
from app.api.upload import router as upload_router
from app.api.retrive import router as retrival_router
from app.api.chat import router as chat_router
from app.rate_limiter import install_rate_limiter
# from app.api.benchmark import router as benchmark_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    
    yield
    
    await close_db()

app = FastAPI(
    title="Finex backend",
    lifespan=lifespan
)

# --- Rate Limiting ---
install_rate_limiter(app)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(upload_router)
app.include_router(retrival_router)
app.include_router(chat_router)
# app.include_router(benchmark_router)  # Disabled for security

@app.get("/")
def read_root():
    return {"status": "ok", "service": "backend"}


# @app.get("/health")
# def health_check():
#     return {"status": "healthy"}
