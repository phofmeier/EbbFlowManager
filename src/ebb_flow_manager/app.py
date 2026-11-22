# FastAPI imports will be handled by uvicorn
import logging
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for controllers (simulating the Panel app state)
controllers: Dict[int, Dict] = {}

# Mock data for initial controllers
initial_controllers = {
    1: {
        "name": "Controller 1",
        "status": "Active",
        "config": {},
        "heap_size": 1024,
        "light_intensity": 50,
        "pump_time": [],
    },
    2: {
        "name": "Controller 2",
        "status": "Inactive",
        "config": {},
        "heap_size": 2048,
        "light_intensity": 75,
        "pump_time": [],
    },
}

controllers.update(initial_controllers)

# Define app at the top of the file
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Ebb Flow Manager API (FastAPI)", "version": "1.0"}


@app.get("/controllers/")
async def get_controllers():
    return list(controllers.keys())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
