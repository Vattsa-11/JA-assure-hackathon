from fastapi import FastAPI

app = FastAPI(title="JA Assure AI Marketing Agent")

@app.get("/")
def read_root():
    return {"status": "ok"}
