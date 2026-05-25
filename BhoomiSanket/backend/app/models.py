from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from geoalchemy2 import Geometry

# --- 1. ADMINISTRATIVE HIERARCHY ---

class Country(Base):
    __tablename__ = 'country'
    country_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    
    states = relationship("State", back_populates="country")

class State(Base):
    __tablename__ = 'state'
    state_code = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey('country.country_id'))
    name = Column(String(100), nullable=False)
    
    country = relationship("Country", back_populates="states")
    districts = relationship("District", back_populates="state")

class District(Base):
    __tablename__ = 'districts'
    state_code = Column(Integer, ForeignKey('state.state_code'), primary_key=True)
    district_code = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    
    state = relationship("State", back_populates="districts")
    villages = relationship("Village", 
                            primaryjoin="District.district_code == Village.district_id",
                            foreign_keys="[Village.district_id]",
                            back_populates="district",
                            viewonly=True)
    summaries = relationship("DistrictSoilSummary", 
                             primaryjoin="District.district_code == DistrictSoilSummary.district_id",
                             foreign_keys="[DistrictSoilSummary.district_id]",
                             back_populates="district",
                             viewonly=True)

class Village(Base):
    __tablename__ = 'village'
    village_id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer) # Joined via district_code in districts
    name = Column(String(100), nullable=False)
    state_name = Column(String(100))
    district_name = Column(String(100))
    
    district = relationship("District", 
                            primaryjoin="Village.district_id == District.district_code",
                            foreign_keys=[district_id],
                            back_populates="villages",
                            viewonly=True)
    farms = relationship("Farm", back_populates="village")

# --- 2. FARMING SYSTEM ---

class Farmer(Base):
    __tablename__ = 'farmer'
    farmer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150))
    mobile = Column(String(15), unique=True, index=True)
    aadhaar_encrypted = Column(String) # Encrypted
    password = Column(String) # For authentication
    gender = Column(String(20), nullable=True)
    dob = Column(DateTime, nullable=True)
    
    farms = relationship("Farm", back_populates="farmer")

class Farm(Base):
    __tablename__ = 'farm'
    farm_id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey('farmer.farmer_id'))
    village_id = Column(Integer, ForeignKey('village.village_id'))
    farm_name = Column(String(150))
    plot_number = Column(String(100), nullable=True)
    area_ha = Column(Float)
    geom = Column(Geometry('GEOMETRY', srid=4326))
    
    farmer = relationship("Farmer", back_populates="farms")
    village = relationship("Village", back_populates="farms")
    crops = relationship("FarmCrop", back_populates="farm")
    soil_samples = relationship("SoilSample", back_populates="farm")
    shs_scores = relationship("SoilHealthScore", back_populates="farm")
    weather_data = relationship("WeatherData", back_populates="farm")
    recommendations = relationship("CropRecommendation", back_populates="farm")

# --- 3. CROP MANAGEMENT ---

class CropMaster(Base):
    __tablename__ = 'crop_master'
    crop_id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String(100))
    category = Column(String(50))
    
    farm_crops = relationship("FarmCrop", back_populates="crop")

class FarmCrop(Base):
    __tablename__ = 'farm_crop'
    farm_crop_id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farm.farm_id'))
    crop_id = Column(Integer, ForeignKey('crop_master.crop_id'))
    season = Column(String(20))
    year = Column(Integer)
    sowing_date = Column(DateTime)
    harvest_date = Column(DateTime)
    
    farm = relationship("Farm", back_populates="crops")
    crop = relationship("CropMaster", back_populates="farm_crops")

# --- 4. SOIL SAMPLING PIPELINE ---

class SoilSample(Base):
    __tablename__ = 'soil_sample'
    soil_sample_id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farm.farm_id'), nullable=True)
    village_id = Column(Integer, ForeignKey('village.village_id'), nullable=True)
    sample_date = Column(DateTime, default=func.now())
    stage = Column(String(50)) # e.g. Germination, Booting, Ripening
    geom = Column(Geometry('POINT', srid=4326))
    
    farm = relationship("Farm", back_populates="soil_samples")
    parameter_values = relationship("SoilParameterValue", back_populates="sample")

class SoilParameterMaster(Base):
    __tablename__ = 'soil_parameter_master'
    parameter_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    unit = Column(String(20))
    ideal_min = Column(Float)
    ideal_max = Column(Float)
    weight = Column(Float)
    
    values = relationship("SoilParameterValue", back_populates="parameter")

class SoilParameterValue(Base):
    __tablename__ = 'soil_parameter_value'
    param_value_id = Column(Integer, primary_key=True, index=True)
    soil_sample_id = Column(Integer, ForeignKey('soil_sample.soil_sample_id'))
    parameter_id = Column(Integer, ForeignKey('soil_parameter_master.parameter_id'))
    value = Column(Float)
    
    sample = relationship("SoilSample", back_populates="parameter_values")
    parameter = relationship("SoilParameterMaster", back_populates="values")

# --- 5. AI / SHS SYSTEM ---

class ScoreModel(Base):
    __tablename__ = 'score_model'
    score_model_id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100))
    description = Column(String)
    created_at = Column(DateTime, default=func.now())
    
    scores = relationship("SoilHealthScore", back_populates="model")

class SoilHealthScore(Base):
    __tablename__ = 'soil_health_score'
    soil_health_score_id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farm.farm_id'), nullable=True)
    soil_sample_id = Column(Integer, ForeignKey('soil_sample.soil_sample_id'), nullable=True)
    score_model_id = Column(Integer, ForeignKey('score_model.score_model_id'), nullable=True)
    score_value = Column(Float)
    score_category = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    farm = relationship("Farm", back_populates="shs_scores")
    sample = relationship("SoilSample")
    model = relationship("ScoreModel", back_populates="scores")
    components = relationship("SoilScoreComponent", back_populates="shs")

class SoilScoreComponent(Base):
    __tablename__ = 'soil_score_component'
    soil_score_component_id = Column(Integer, primary_key=True, index=True)
    soil_health_score_id = Column(Integer, ForeignKey('soil_health_score.soil_health_score_id'))
    parameter_id = Column(Integer, ForeignKey('soil_parameter_master.parameter_id'))
    normalized_score = Column(Float)
    weight = Column(Float)
    contribution = Column(Float)
    
    shs = relationship("SoilHealthScore", back_populates="components")

# --- 6. WEATHER SYSTEM ---

class WeatherData(Base):
    __tablename__ = 'weather_data'
    weather_id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farm.farm_id'))
    date = Column(DateTime)
    rainfall = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    
    farm = relationship("Farm", back_populates="weather_data")

# --- 7. CROP RECOMMENDATION ENGINE ---

class CropRecommendation(Base):
    __tablename__ = 'crop_recommendation'
    recommendation_id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farm.farm_id'))
    farmer_id = Column(Integer, ForeignKey('farmer.farmer_id'), nullable=True)
    crop_id = Column(Integer, ForeignKey('crop_master.crop_id'))
    suitability_score = Column(Float)
    recommended = Column(Boolean)
    
    farm = relationship("Farm", back_populates="recommendations")

# --- 8. GIS AGGREGATION SYSTEM ---

class DistrictSoilSummary(Base):
    __tablename__ = 'district_soil_summary'
    district_id = Column(Integer, primary_key=True)
    year = Column(Integer, primary_key=True)
    avg_score = Column(Float)
    geom = Column(Geometry('POINT', srid=4326))
    
    district = relationship("District", 
                            primaryjoin="DistrictSoilSummary.district_id == District.district_code",
                            foreign_keys=[district_id],
                            back_populates="summaries",
                            viewonly=True)

# --- 9. GIS VISUALIZATION CACHE TABLE ---

class LatLonSuitability(Base):
    __tablename__ = 'latlon_suitability'
    id = Column(Integer, primary_key=True, index=True)
    
    farm_id = Column(Integer, ForeignKey('farm.farm_id'), nullable=False)
    soil_sample_id = Column(Integer, ForeignKey('soil_sample.soil_sample_id'), nullable=False)
    
    state_name = Column(String(100))
    district_name = Column(String(100))
    village_name = Column(String(100))
    
    stage = Column(String(20), nullable=False)
    
    lat = Column(Float)
    lon = Column(Float)
    
    # Flat parameters for fast frontend caching
    nitrogen = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    moisture = Column(Float)
    ph = Column(Float)
    organic_carbon = Column(Float)
    temperature = Column(Float)
    
    shs_score = Column(Float)
    shs_category = Column(String(20))
    
    geom = Column(Geometry('POINT', srid=4326))
    
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('farm_id', 'soil_sample_id', 'stage', name='_farm_sample_stage_uc'),
    )

# --- Shared columns mixin for farmer result tables ---
class _FarmerResultBase:
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey('farmer.farmer_id'), index=True, nullable=True)
    lat = Column(Float)
    lon = Column(Float)
    nitrogen = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    ph = Column(Float)
    moisture = Column(Float)
    organic_carbon = Column(Float)
    temperature = Column(Float)
    created_at = Column(DateTime, default=func.now())

class FarmerResultGerm(_FarmerResultBase, Base):
    __tablename__ = 'farmer_result_germ'
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey('farmer.farmer_id'), index=True, nullable=True)
    lat = Column(Float)
    lon = Column(Float)
    nitrogen = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    ph = Column(Float)
    moisture = Column(Float)
    organic_carbon = Column(Float)
    temperature = Column(Float)
    germ_shs = Column(Float)
    created_at = Column(DateTime, default=func.now())

class FarmerResultBoot(_FarmerResultBase, Base):
    __tablename__ = 'farmer_result_boot'
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey('farmer.farmer_id'), index=True, nullable=True)
    lat = Column(Float)
    lon = Column(Float)
    nitrogen = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    ph = Column(Float)
    moisture = Column(Float)
    organic_carbon = Column(Float)
    temperature = Column(Float)
    boot_shs = Column(Float)
    created_at = Column(DateTime, default=func.now())

class FarmerResultRip(_FarmerResultBase, Base):
    __tablename__ = 'farmer_result_rip'
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey('farmer.farmer_id'), index=True, nullable=True)
    lat = Column(Float)
    lon = Column(Float)
    nitrogen = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    ph = Column(Float)
    moisture = Column(Float)
    organic_carbon = Column(Float)
    temperature = Column(Float)
    rip_shs = Column(Float)
    created_at = Column(DateTime, default=func.now())

class FarmerAdvisory(Base):
    __tablename__ = 'farmer_advisory'
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey('farmer.farmer_id'), index=True)
    result_id = Column(Integer, index=True) # ID from the respective stage table
    stage = Column(String(50)) # germination, booting, ripening
    lat = Column(Float)
    lon = Column(Float)
    shs_score = Column(Float)
    shs_category = Column(String(50))
    advisory_text = Column(String) # JSON string containing per-parameter advice
    overall_advice = Column(String)
    created_at = Column(DateTime, default=func.now())
