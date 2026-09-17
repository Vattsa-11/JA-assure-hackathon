from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.review import router as review_router
from app.api.pipeline import router as pipeline_router

app = FastAPI(title="JA Assure AI Marketing Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router)
app.include_router(pipeline_router)

@app.get("/")
def read_root():
    return {"status": "ok"}
