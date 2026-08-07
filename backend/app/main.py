from fastapi import FastAPI

from app.api.upload import router as upload_router

app = FastAPI(
    title="Finex backend"
)


app.include_router(upload_router)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "backend"}


# @app.get("/health")
# def health_check():
#     return {"status": "healthy"}
