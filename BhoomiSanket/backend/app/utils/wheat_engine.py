"""
==========================================================
WHEAT SOIL HEALTH SCORE ENGINE (UNIFIED)
==========================================================
"""

from __future__ import annotations
from typing import Dict, List, Any
import numpy as np
import pandas as pd

GERMINATION_MATRIX = np.array([
    [1,   1/3, 3,   1/3, 3,   3,   5],
    [3,   1,   5,   1,   5,   5,   7],
    [1/3, 1/5, 1,   1/5, 3,   3,   5],
    [3,   1,   5,   1,   5,   5,   7],
    [1/3, 1/5, 1/3, 1/5, 1,   3,   3],
    [1/3, 1/5, 1/3, 1/5, 1/3, 1,   1],
    [1/5, 1/7, 1/5, 1/7, 1/3, 1,   1]
], dtype=float)

BOOTING_MATRIX = np.array([
    [1,   3,   3,   1,   5,   5,   5,   1],
    [1/3, 1,   1,   1/3, 3,   3,   3,   1/3],
    [1/3, 1,   1,   1/3, 3,   3,   3,   1/3],
    [1,   3,   3,   1,   5,   5,   5,   1],
    [1/5, 1/3, 1/3, 1/5, 1,   3,   3,   1/5],
    [1/5, 1/3, 1/3, 1/5, 1/3, 1,   1,   1/5],
    [1/5, 1/3, 1/3, 1/5, 1/3, 1,   1,   1/5],
    [1,   3,   3,   1,   5,   5,   5,   1]
], dtype=float)

RIPENING_MATRIX = np.array([
    [1,   3,   1/3, 1/3, 3,   3,   1/5, 1/3],
    [1/3, 1,   1/5, 1/5, 3,   3,   1/7, 1/5],
    [3,   5,   1,   1,   5,   5,   1/3, 1],
    [3,   5,   1,   1,   5,   5,   1/3, 1],
    [1/3, 1/3, 1/5, 1/5, 1,   3,   1/7, 1/5],
    [1/3, 1/3, 1/5, 1/5, 1/3, 1,   1/7, 1/5],
    [5,   7,   3,   3,   7,   7,   1,   3],
    [3,   5,   1,   1,   5,   5,   1/3, 1]
], dtype=float)

RI_VALUES = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
}

def nitrogen(n: float) -> float:
    if n < 150: return 0.0
    if n < 280: return (n - 150) / 130
    return 1.0

def phosphorus(p: float) -> float:
    if p < 10: return 0.0
    if p < 20: return (p - 10) / 10
    return 1.0

def potassium(k: float) -> float:
    if k < 110: return 0.0
    if k < 150: return (k - 110) / 40
    return 1.0

def moisture_g(m: float) -> float:
    if m < 10: return 0.0
    if m < 20: return (m - 10) / 10
    return 1.0

def moisture_r(m: float) -> float:
    if m < 10: return 0.0
    if m < 18: return (m - 10) / 8
    if m <= 25: return 1.0
    if m <= 35: return (35 - m) / 10
    return 0.0

def ph_membership(ph: float) -> float:
    if ph < 5.5: return 0.0
    if ph < 6.0: return (ph - 5.5) / 0.5
    if ph <= 7.5: return 1.0
    if ph <= 8.0: return (8.0 - ph) / 0.5
    return 0.0

def oc_membership(oc: float) -> float:
    if oc < 0.3: return 0.0
    if oc < 0.6: return (oc - 0.3) / 0.3
    return 1.0

def temp_g(t: float) -> float:
    if t < 10: return 0.0
    if t < 18: return (t - 10) / 8
    if t <= 25: return 1.0
    return 0.5

def temp_r(t: float) -> float:
    if t < 15: return 0.3
    if t < 20: return (t - 15) / 5
    if t <= 25: return 1.0
    if t <= 30: return (30 - t) / 5
    return 0.0

def ndvi(n: float) -> float:
    if n < 0.5: return 0.0
    if n < 0.7: return (n - 0.5) / 0.2
    if n <= 0.9: return 1.0
    return 0.5

def ndvi_r(n: float) -> float:
    if n < 0.4: return 0.0
    if n < 0.6: return (n - 0.4) / 0.2
    if n <= 0.8: return 1.0
    return 0.7

class WheatSHSEngine:
    def __init__(self, stage: str):
        self.stage = stage.lower().strip()
        if self.stage == "germination":
            self.matrix = GERMINATION_MATRIX
            self.criteria = ["N", "P", "K", "Moisture", "pH", "OC", "Temp"]
        elif self.stage == "booting":
            self.matrix = BOOTING_MATRIX
            self.criteria = ["N", "P", "K", "Moisture", "pH", "OC", "Temp", "NDVI"]
        elif self.stage == "ripening":
            self.matrix = RIPENING_MATRIX
            self.criteria = ["N", "P", "K", "Moisture", "pH", "OC", "Temp", "NDVI"]
        else:
            raise ValueError("Invalid stage. Choose from: germination, booting, ripening")

        self.weights = self._compute_weights()
        self.consistency_ratio = self._compute_consistency_ratio()

    def _compute_weights(self) -> np.ndarray:
        col_sum = self.matrix.sum(axis=0)
        norm_matrix = self.matrix / col_sum
        return norm_matrix.mean(axis=1)

    def _compute_consistency_ratio(self) -> float:
        n = self.matrix.shape[0]
        weighted_sum = self.matrix @ self.weights
        lambda_max = float(np.mean(weighted_sum / self.weights))
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        ri = RI_VALUES.get(n, 1.49)
        if ri == 0: return 0.0
        return float(ci / ri)

    def _compute_shs(self, fuzzy_scores: np.ndarray) -> float:
        return float(np.dot(fuzzy_scores, self.weights) * 100)

    def _build_fuzzy_scores(self, sample: Dict[str, Any]) -> np.ndarray:
        s = {k: float(v) for k, v in sample.items() if k in self.criteria}
        if self.stage == "germination":
            fuzzy = np.array([
                nitrogen(s["N"]), phosphorus(s["P"]), potassium(s["K"]),
                moisture_g(s["Moisture"]), ph_membership(s["pH"]),
                oc_membership(s["OC"]), temp_g(s["Temp"]),
            ], dtype=float)
        elif self.stage == "booting":
            fuzzy = np.array([
                nitrogen(s["N"]), phosphorus(s["P"]), potassium(s["K"]),
                moisture_g(s["Moisture"]), ph_membership(s["pH"]),
                oc_membership(s["OC"]), temp_g(s["Temp"]), ndvi(s["NDVI"]),
            ], dtype=float)
        else:
            fuzzy = np.array([
                nitrogen(s["N"]), phosphorus(s["P"]), potassium(s["K"]),
                moisture_r(s["Moisture"]), ph_membership(s["pH"]),
                oc_membership(s["OC"]), temp_r(s["Temp"]), ndvi_r(s["NDVI"]),
            ], dtype=float)
        return fuzzy

    def predict(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        fuzzy = self._build_fuzzy_scores(sample)
        score = self._compute_shs(fuzzy)
        
        # Categorize
        if score >= 75: category = "Good"
        elif score >= 50: category = "Fair"
        else: category = "Poor"

        return {
            "stage": self.stage,
            "SHS": round(score, 2),
            "Category": category,
            "CR": round(self.consistency_ratio, 4),
        }
