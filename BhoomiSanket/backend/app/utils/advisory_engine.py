import json
from sqlalchemy.orm import Session
from app.models import SoilParameterMaster

class AdvisoryEngine:
    def __init__(self, db: Session):
        self.db = db
        # Cache parameter bounds
        self.params = {p.name: p for p in self.db.query(SoilParameterMaster).all()}
        self.name_map = {
            "nitrogen": "N",
            "phosphorus": "P",
            "potassium": "K",
            "ph": "pH",
            "moisture": "Moisture",
            "organic_carbon": "OC",
            "temperature": "Temp"
        }

    def _get_advice(self, param_key: str, value: float):
        db_name = self.name_map.get(param_key)
        if not db_name or db_name not in self.params:
            return {"status": "Unknown", "advice": "No data available."}
        
        param = self.params[db_name]
        min_val = param.ideal_min
        max_val = param.ideal_max
        
        if value < min_val:
            diff = round(min_val - value, 2)
            if param_key == "nitrogen":
                advice = f"Deficient by {diff} {param.unit}. Apply 10-20 kg/ha of Urea."
            elif param_key == "phosphorus":
                advice = f"Deficient by {diff} {param.unit}. Apply 15-25 kg/ha of DAP."
            elif param_key == "potassium":
                advice = f"Deficient by {diff} {param.unit}. Apply 10-15 kg/ha of MOP."
            elif param_key == "ph":
                advice = f"Acidic soil. Apply agricultural lime."
            elif param_key == "moisture":
                advice = f"Low moisture. Immediate irrigation required."
            elif param_key == "organic_carbon":
                advice = f"Low organic carbon. Add compost or FYM (Farm Yard Manure)."
            elif param_key == "temperature":
                advice = f"Temperature is below ideal range. Delay sowing or use mulching."
            else:
                advice = f"Deficient. Increase by {diff} {param.unit}."
            return {"status": "Deficient", "advice": advice, "ideal_min": min_val, "ideal_max": max_val}
            
        elif value > max_val:
            diff = round(value - max_val, 2)
            if param_key == "nitrogen":
                advice = f"Excess by {diff} {param.unit}. Reduce nitrogen fertilizer usage."
            elif param_key == "phosphorus":
                advice = f"Excess by {diff} {param.unit}. Limit phosphorus application."
            elif param_key == "potassium":
                advice = f"Excess by {diff} {param.unit}. Limit potassium application."
            elif param_key == "ph":
                advice = f"Alkaline soil. Apply gypsum or elemental sulfur to lower pH."
            elif param_key == "moisture":
                advice = f"High moisture. Ensure proper field drainage to prevent waterlogging."
            elif param_key == "organic_carbon":
                advice = f"Good organic carbon levels."
            elif param_key == "temperature":
                advice = f"Temperature is above ideal range. Ensure adequate moisture."
            else:
                advice = f"Excess. Decrease by {diff} {param.unit}."
            return {"status": "Excess", "advice": advice, "ideal_min": min_val, "ideal_max": max_val}
            
        else:
            return {"status": "Good", "advice": "Values are in ideal range. No corrective action needed.", "ideal_min": min_val, "ideal_max": max_val}

    def generate(self, inputs: dict, shs_score: float):
        parameters = []
        for key, val in inputs.items():
            if val is None:
                continue
            res = self._get_advice(key, val)
            parameters.append({
                "name": key.replace("_", " ").title(),
                "value": val,
                "status": res["status"],
                "advice": res["advice"],
                "ideal_min": res.get("ideal_min"),
                "ideal_max": res.get("ideal_max")
            })
            
        if shs_score >= 78:
            cat = "Excellent"
            overall = "Soil is in excellent condition for this stage."
        elif shs_score >= 75:
            cat = "Good"
            overall = "Good soil health. Minor improvements recommended."
        elif shs_score >= 50:
            cat = "Moderate"
            overall = "Moderate soil health. Key deficiencies need attention."
        else:
            cat = "Poor"
            overall = "Poor soil health. Immediate remediation required before proceeding."
            
        return {
            "shs_category": cat,
            "overall_advice": overall,
            "parameters": parameters
        }
