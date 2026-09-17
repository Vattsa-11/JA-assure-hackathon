from fastapi import FastAPI
from app.api.review import router as review_router
from app.api.pipeline import router as pipeline_router

app = FastAPI(title="JA Assure AI Marketing Agent")

app.include_router(review_router)
app.include_router(pipeline_router)

@app.get("/")
def read_root():
    return {"status": "ok"}
