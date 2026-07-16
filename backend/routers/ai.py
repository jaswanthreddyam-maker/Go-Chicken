from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from datetime import date

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Forecasting"],
)

class SalesData(BaseModel):
    date: str
    actual: float
    predicted: float

class ClusterData(BaseModel):
    region: str
    x: float
    y: float
    z: float
    fill: str

class ForecastData(BaseModel):
    target_date: str
    predicted_demand_kg: float
    weather_condition: str
    reasoning: str

@router.get("/sales-comparison", response_model=List[SalesData])
async def get_sales_comparison():
    return [
        {"date": "Mon", "actual": 4200, "predicted": 4100},
        {"date": "Tue", "actual": 4800, "predicted": 4600},
        {"date": "Wed", "actual": 3900, "predicted": 4050},
        {"date": "Thu", "actual": 5100, "predicted": 5300},
        {"date": "Fri", "actual": 5800, "predicted": 5750},
        {"date": "Sat", "actual": 6200, "predicted": 6100},
        {"date": "Sun", "actual": 5900, "predicted": 5850}
    ]

@router.get("/demand-clusters", response_model=List[ClusterData])
async def get_demand_clusters():
    return [
        {"region": "North Zone", "x": 120, "y": 80, "z": 200, "fill": "#111111"},
        {"region": "South Zone", "x": 180, "y": 90, "z": 300, "fill": "#666666"},
        {"region": "East Zone", "x": 220, "y": 110, "z": 150, "fill": "#999999"},
        {"region": "West Zone", "x": 150, "y": 75, "z": 250, "fill": "#CCCCCC"}
    ]

@router.get("/forecast/today", response_model=ForecastData)
async def get_forecast_today():
    return {
        "target_date": date.today().isoformat(),
        "predicted_demand_kg": 5240,
        "weather_condition": "Sunny, 31°C",
        "reasoning": "High confidence based on recent historical trends and lack of weather disruptions."
    }
