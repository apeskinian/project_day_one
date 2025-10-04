from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lightswarm import lightswarm_command
from sk6812 import sk6812_command

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
