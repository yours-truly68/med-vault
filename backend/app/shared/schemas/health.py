from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app: str
    version: str
    environment: str
    database: Literal["connected", "disconnected"]
    redis: Literal["connected", "disconnected"] = "disconnected"
    queue: Literal["connected", "disconnected"] = "disconnected"
    worker: Literal["registered", "unregistered"] = "unregistered"
