"""
FastAPI application for controlling lighting systems (Lightswarm and SK6812).

This service provides:
- Static file serving for frontend assets and resources.
- Health check endpoint for monitoring.
- REST endpoints to send commands to Lightswarm / SK6812 lighting controllers.
"""

# Standard imports:
import os
# Third party imports:
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
# Local imports:
from lightswarm import lightswarm_command
from sk6812 import sk6812_command

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",  # Change ports to match requirements.
        "http://127.0.0.1:8000",  # Change ports to match requirements.
        "http://localhost:5173",  # Change ports to match requirements.
        "http://127.0.0.1:5173",  # Change ports to match requirements.
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount root files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Mount static assets (JS, CSS, images)
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
# Mount hdri files for 3D model environment
app.mount("/hdri", StaticFiles(directory="static/hdri"), name="hdri")
# Mount images for buildings
app.mount("/images", StaticFiles(directory="static/images"), name="images")
# Mount qr-codes
app.mount(
    "/qr-codes", StaticFiles(directory="static/qr-codes"), name="qr-codes"
)


# Serve index.html at root
@app.get("/")
def serve_index():
    """
    Serve the main frontend entry point.

    Returns:
        FileResponse: The `index.html` file located in the `static` directory.
    """
    return FileResponse(os.path.join("static", "index.html"))


class LightswarmCommand(BaseModel):
    """
    Schema for Lightswarm lighting commands.

    Attributes:
        name (str): Name of the command or preset.
        channels (list): Target channels for the command.
        action (str): Action to perform (e.g., "on", "off", "fade").
        level (int | None): Optional brightness level.
        interval (int | None): Optional interval for repeating actions.
        step (int | None): Optional step size for transitions.
        pseudo_address (int | None): Optional pseudo-address for addressing.
    """
    name: str
    channels: list
    action: str
    level: int | None = None
    interval: int | None = None
    step: int | None = None
    pseudo_address: int | None = None


class SK6812Command(BaseModel):
    """
    Schema for SK6812 LED strip commands.

    Attributes:
        name (str): Name of the command or preset.
        channels (list): Target channels for the command.
        colour (str): Colour value (rgbw value (255, 255, 255, 255)).
        brightness (float): Brightness level (0.0–1.0).
        effect (str): Lighting effect to apply (e.g., "blink", "fade").
    """
    name: str
    channels: list
    colour: str
    brightness: float
    effect: str


@app.post("/lightswarm")
def lightswarm(command: LightswarmCommand):
    """
    Endpoint to send a Lightswarm command.

    Args:
        command (LightswarmCommand): Parsed command payload.

    Returns:
        dict: Status message indicating success or error.
    """
    try:
        lightswarm_command(command.model_dump())
        return {'status': 'Success'}
    except Exception as error:
        return {'status': f'Error: {error}'}


@app.post("/sk6812")
def sk6812(command: SK6812Command):
    """
    Endpoint to send a SK6812 LED strip command.

    Args:
        command (SK6812Command): Parsed command payload.

    Returns:
        dict: Status message indicating success or error.
    """
    try:
        sk6812_command(command.model_dump())
        return {'status': 'Success'}
    except Exception as error:
        return {'status': f'Error: {error}'}
