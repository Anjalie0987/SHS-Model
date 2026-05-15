from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class SoilAnalysisRequest(BaseModel):
    farmer_name: str
    mobile: Optional[str] = "0000000000"
    field_id: str
    state: str
    district: str
    village: Optional[str] = "Default Village"
    crop_type: Optional[str] = "Wheat"
    season: str
    field_area: float
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    moisture: Optional[float] = 20.0
    organic_carbon: Optional[float] = 0.5
    temperature: Optional[float] = 22.0
    ndvi: Optional[float] = 0.7
    coordinates: Optional[Any] = None # Expecting list or dict or null

class SoilAnalysisResponse(BaseModel):
    snsi_score: float
    soil_status: str
    nutrient_levels: Dict[str, Any]
    recommendations: List[str]
    map_classification: str
    health_status: str
