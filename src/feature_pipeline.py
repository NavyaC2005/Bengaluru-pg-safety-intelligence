"""
Feature Engineering & Transformation Pipeline
Standardizes feature preprocessing for Scikit-learn regressors and web predictions.
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline

CATEGORICAL_FEATURES = [
    'locality',
    'room_type',
    'food_option',
    'wifi',
    'ac',
    'bathroom_type'
]

AMENITY_FEATURE_COLS = [
    'amenity_lift',
    'amenity_housekeeping',
    'amenity_cctv',
    'amenity_power_backup',
    'amenity_gym',
    'amenity_study_area',
    'amenity_parking',
    'amenity_laundry',
    'amenity_common_kitchen',
    'amenity_biometric_entry'
]

NUMERICAL_FEATURES = ['amenity_count']

ALL_MODEL_FEATURES = CATEGORICAL_FEATURES + AMENITY_FEATURE_COLS + NUMERICAL_FEATURES

def create_feature_preprocessor() -> ColumnTransformer:
    """Creates a ColumnTransformer encoding categorical features with OneHotEncoder."""
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES),
            ('amenities', 'passthrough', AMENITY_FEATURE_COLS + NUMERICAL_FEATURES)
        ],
        remainder='drop'
    )
    return preprocessor

def prepare_feature_dataframe(input_dict: dict) -> pd.DataFrame:
    """
    Transforms a single listing dictionary (e.g., from web API or CLI)
    into a standardized single-row DataFrame ready for the ML pipeline.
    """
    # Normalize inputs
    locality = str(input_dict.get('locality', 'BTM Layout')).strip().title()
    room_type = str(input_dict.get('room_type', 'Double Sharing')).strip()
    food_option = str(input_dict.get('food_option', 'Available at extra cost')).strip()
    wifi = 'Yes' if str(input_dict.get('wifi', 'No')).lower() in ['yes', '1', 'true'] else 'No'
    ac = 'Yes' if str(input_dict.get('ac', 'No')).lower() in ['yes', '1', 'true'] else 'No'
    bathroom_type = str(input_dict.get('bathroom_type', 'Attached')).strip()
    
    amenities_list = input_dict.get('amenities', [])
    if isinstance(amenities_list, str):
        amenities_list = [a.strip() for a in amenities_list.split(';') if a.strip()]
        
    amenities_lower = [a.lower() for a in amenities_list]
    
    row = {
        'locality': locality,
        'room_type': room_type,
        'food_option': food_option,
        'wifi': wifi,
        'ac': ac,
        'bathroom_type': bathroom_type
    }
    
    count = 0
    for col in AMENITY_FEATURE_COLS:
        name_clean = col.replace('amenity_', '').replace('_', ' ')
        has_it = 1 if any(name_clean in a for a in amenities_lower) or input_dict.get(col, 0) in [1, '1', True] else 0
        row[col] = has_it
        count += has_it
        
    row['amenity_count'] = count
    return pd.DataFrame([row])
