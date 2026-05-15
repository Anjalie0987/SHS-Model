from app.database import SessionLocal
from app import models
from app.utils.wheat_engine import WheatSHSEngine
from geoalchemy2.functions import ST_X, ST_Y
import logging

logger = logging.getLogger(__name__)

class SHSService:
    @staticmethod
    def process_soil_sample(soil_sample_id: int):
        """
        Main entry point for background SHS processing.
        Calculates scores for all stages and updates the GIS cache.
        """
        db = SessionLocal()
        try:
            sample = db.query(models.SoilSample).filter(models.SoilSample.soil_sample_id == soil_sample_id).first()
            if not sample:
                logger.error(f"Soil sample {soil_sample_id} not found")
                return

            farm = db.query(models.Farm).filter(models.Farm.farm_id == sample.farm_id).first() if sample.farm_id else None
            # We continue even if farm is None, as long as we have a village or sample geometry

            # Pivot EAV parameters
            params = db.query(models.SoilParameterValue, models.SoilParameterMaster.name)\
                .join(models.SoilParameterMaster)\
                .filter(models.SoilParameterValue.soil_sample_id == soil_sample_id).all()
            
            sample_data = {p.name: p.SoilParameterValue.value for p in params}
            
            required = ["N", "P", "K", "Moisture", "pH", "OC", "Temp", "NDVI"]
            for r in required:
                if r not in sample_data:
                    sample_data[r] = 0.0

            # Get Location Names
            v_id = sample.village_id if sample.village_id else (farm.village_id if farm else None)
            village = db.query(models.Village).filter(models.Village.village_id == v_id).first()
            district = db.query(models.District).filter(models.District.district_code == village.district_id).first() if village else None
            state = db.query(models.State).filter(models.State.state_code == district.state_code).first() if district else None

            # Get Coordinates
            geom_source = sample.geom if sample.geom is not None else (farm.geom if farm else None)
            coords = db.query(ST_X(geom_source), ST_Y(geom_source)).first() if geom_source is not None else (0.0, 0.0)
            lon, lat = coords if coords else (0.0, 0.0)

            # Process all 3 stages
            stages = ["Germination", "Booting", "Ripening"]
            for stage in stages:
                engine = WheatSHSEngine(stage)
                result = engine.predict(sample_data)
                
                shs_entry = db.query(models.SoilHealthScore).filter(
                    models.SoilHealthScore.soil_sample_id == soil_sample_id,
                    models.SoilHealthScore.score_category == stage
                ).first()
                
                if not shs_entry:
                    shs_entry = models.SoilHealthScore(
                        farm_id=farm.farm_id if farm else None,
                        soil_sample_id=soil_sample_id,
                        score_value=result["SHS"],
                        score_category=stage,
                    )
                    db.add(shs_entry)
                else:
                    shs_entry.score_value = result["SHS"]
                
                db.flush()

                # UPSERT into LatLonSuitability
                cache_entry = db.query(models.LatLonSuitability).filter(
                    models.LatLonSuitability.soil_sample_id == soil_sample_id,
                    models.LatLonSuitability.stage == stage
                ).first()

                if not cache_entry:
                    cache_entry = models.LatLonSuitability(
                        farm_id=farm.farm_id if farm else None,
                        soil_sample_id=soil_sample_id,
                        stage=stage,
                        state_name=state.name if state else "Unknown",
                        district_name=district.name if district else "Unknown",
                        village_name=village.name if village else "Unknown",
                        lat=lat,
                        lon=lon,
                        geom=geom_source,
                        nitrogen=sample_data.get("N"),
                        phosphorus=sample_data.get("P"),
                        potassium=sample_data.get("K"),
                        moisture=sample_data.get("Moisture"),
                        ph=sample_data.get("pH"),
                        organic_carbon=sample_data.get("OC"),
                        temperature=sample_data.get("Temp"),
                        shs_score=result["SHS"],
                        shs_category=result["Category"]
                    )
                    db.add(cache_entry)
                else:
                    cache_entry.shs_score = result["SHS"]
                    cache_entry.shs_category = result["Category"]
                    cache_entry.lat = lat
                    cache_entry.lon = lon
                    cache_entry.geom = geom_source
                    cache_entry.nitrogen = sample_data.get("N")
                    cache_entry.phosphorus = sample_data.get("P")
                    cache_entry.potassium = sample_data.get("K")
                    cache_entry.moisture = sample_data.get("Moisture")
                    cache_entry.ph = sample_data.get("pH")
                    cache_entry.organic_carbon = sample_data.get("OC")
                    cache_entry.temperature = sample_data.get("Temp")

            db.commit()
            print(f"BACKGROUND TASK SUCCESS: Processed SHS for sample {soil_sample_id}")
            
        except Exception as e:
            db.rollback()
            print(f"BACKGROUND TASK ERROR: {e}")
        finally:
            db.close()
