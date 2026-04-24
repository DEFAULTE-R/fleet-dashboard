from pydantic import BaseModel, Field

class SensorData(BaseModel):
    cpu_usage: float = Field(..., ge=0, le=100)
    temperature_c: float
    memory_usage: float = Field(..., ge=0, le=100)
    error_count: int = Field(..., ge=0)
    tasks_completed: int = Field(..., ge=0)
    uptime_seconds: int = Field(..., ge=0)
