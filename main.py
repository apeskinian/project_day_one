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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static assets (JS, CSS, images)
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")


# Serve root files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Serve index.html at root
@app.get("/")
def serve_index():
    return FileResponse(os.path.join("static", "index.html"))


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
