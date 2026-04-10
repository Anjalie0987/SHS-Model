import pandas as pd
import json

df = pd.read_csv('d:/CROP2/CROP2/BhoomiSanket/Maharashtra_Germination_8000_NoSpatial.csv')
cols = ['N', 'P', 'K', 'pH', 'OC', 'Moisture', 'Temp']
ranges = {}

for col in cols:
    ranges[col] = {
        'min': float(df[col].min()),
        'max': float(df[col].max())
    }

print(json.dumps(ranges, indent=2))
