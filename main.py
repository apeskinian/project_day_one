# uvicorn main:app --host localhost --port 8000
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from lightswarm import lightswarm_command
from sk6812 import sk6812_command

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve root files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve static assets (JS, CSS, images)
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

# Serve hdri files for 3D model environment
app.mount("/hdri", StaticFiles(directory="static/hdri"), name="hdri")

# Serve images for buildings
app.mount("/images", StaticFiles(directory="static/images"), name="images")

# Serve qr-codes
app.mount(
    "/qr-codes", StaticFiles(directory="static/qr-codes"), name="qr-codes"
)


# Serve index.html at root
@app.get("/")
def serve_index():
    return FileResponse(os.path.join("static", "index.html"))


@app.get("/ping")
def health_check():
    return {'status': 'ok'}


class LightswarmCommand(BaseModel):
    name: str
    channels: list
    action: str
    level: int | None = None
    interval: int | None = None
    step: int | None = None
    pseudo_address: int | None = None


class SK6812Command(BaseModel):
    name: str
    channels: list
    colour: str
    brightness: float
    effect: str


@app.post("/lightswarm")
def lightswarm(command: LightswarmCommand):
    try:
        lightswarm_command(command.model_dump())
        return {'status': 'Success'}
    except Exception as error:
        return {'status': f'Error: {error}'}


@app.post("/sk6812")
def sk6812(command: SK6812Command):
    try:
        sk6812_command(command.model_dump())
        return {'status': 'Success'}
    except Exception as error:
        return {'status': f'Error: {error}'}
