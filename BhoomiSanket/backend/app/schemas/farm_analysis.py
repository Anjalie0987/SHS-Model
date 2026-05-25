from pydantic import BaseModel
from typing import Optional, List

class FarmDataResponse(BaseModel):
    farmer_id: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    subdistrict: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lat: Optional[float] = None  # Short alias for frontend
    lon: Optional[float] = None  # Short alias for frontend
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    ph: Optional[float] = None
    organic_carbon: Optional[float] = None
    moisture: Optional[float] = None
    temperature: Optional[float] = None # Added missing field
    shs_germination: Optional[float] = None
    category_germination: Optional[str] = None
    soil_type: Optional[str] = None
    recommended_fertilizer: Optional[str] = None

class StateInfo(BaseModel):
    name: str
    code: int

class DistrictInfo(BaseModel):
    name: str
    code: int
    state_code: int

class SubdistrictInfo(BaseModel):
    name: str
    id: int

class LocationHierarchy(BaseModel):
    states: List[StateInfo]
    districts: dict  # state_code -> List[DistrictInfo]
    subdistricts: Optional[dict] = {} # district_code -> [subdistricts]

class AnalysisResponse(BaseModel):
    data: List[FarmDataResponse]
    message: str
