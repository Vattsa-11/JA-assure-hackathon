import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.dashboard import router as dashboard_router
from app.api.pipeline import router as pipeline_router
from app.api.review import router as review_router

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
app.include_router(dashboard_router)

# Mount media directory for videos
media_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "media"))
if not os.path.exists(media_dir):
    os.makedirs(media_dir)
app.mount("/media", StaticFiles(directory=media_dir), name="media")


@app.get("/")
def read_root():
    return {"status": "ok"}
