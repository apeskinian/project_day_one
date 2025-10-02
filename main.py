from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lightswarm import compile_command

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LightCommand(BaseModel):
    address: int
    action: str
    level: int | None = None
    interval: int | None = None
    step: int | None = None
    pseudo_address: int | None = None


@app.post("/light")
def light_building(command: LightCommand):
    compile_command(command.model_dump())
    return {'status': 'sent', 'command': command}
