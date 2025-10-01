from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Building(BaseModel):
    id: str
    isLit: bool


@app.post("/light")
def light_building(building: Building):
    print(building.isLit)
    if building.isLit is True:
        print(f'Lighting building {building.id}')
        return {'isLit': True, 'id': building.id}
    else:
        print(f'Turning off building {building.id}')
        return {'isLit': False, 'id': building.id}
