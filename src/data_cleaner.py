"""
Data Cleaning & Normalization Module for Bengaluru PG Safety & Price Intelligence
Handles currency parsing, locality normalization, missing value imputation, and amenity extraction.
"""

import re
import pandas as pd
import numpy as np

# Canonical mapping for Bengaluru localities
LOCALITY_MAPPING = {
    'marathahalli': 'Marathahalli',
    'bommanahalli': 'Bommanahalli',
    'rajajinagar': 'Rajajinagar',
    'hebbal': 'Hebbal',
    'jayanagar': 'Jayanagar',
    'banashankari': 'Banashankari',
    'electronic city': 'Electronic City',
    'btm layout': 'BTM Layout',
    'whitefield': 'Whitefield',
    'hsr layout': 'HSR Layout',
    'indiranagar': 'Indiranagar',
    'cv raman nagar': 'CV Raman Nagar',
    'koramangala': 'Koramangala',
    'yelahanka': 'Yelahanka',
    'bellandur': 'Bellandur',
    'mahadevapura': 'Mahadevapura',
}

KNOWN_AMENITIES = [
    'Lift',
    'Housekeeping',
    'CCTV',
    'Power backup',
    'Gym',
    'Study area',
    'Parking',
    'Laundry',
    'Common kitchen',
    'Biometric entry'
]

def clean_currency(val) -> float:
    """Converts dirty currency strings (e.g. '₹13,300', '46,500 INR', '14k') to numeric float."""
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).strip()
    # Check for 'k' / 'K' thousands suffix (e.g. '14k')
    k_match = re.search(r'([\d\.]+)\s*[kK]', val_str)
    if k_match:
        try:
            return float(k_match.group(1)) * 1000.0
        except ValueError:
            pass
            
    # Remove symbols like ₹, INR, commas, spaces
    cleaned = re.sub(r'[^\d\.]', '', val_str)
    try:
        return float(cleaned) if cleaned else np.nan
    except ValueError:
        return np.nan

def normalize_locality(val: str) -> str:
    """Standardizes locality spelling and capitalizations across Bengaluru."""
    if pd.isna(val):
        return 'Unknown'
    cleaned = str(val).strip().lower()
    return LOCALITY_MAPPING.get(cleaned, str(val).strip().title())

def clean_dataset(df_raw: pd.DataFrame) -> (pd.DataFrame, dict):
    """
    Cleans raw PG dataset according to project specifications.
    Returns cleaned dataframe and a summary dictionary of cleaning actions.
    """
    df = df_raw.copy()
    initial_shape = df.shape
    
    # 1. Clean numeric rent and deposit
    df['monthly_rent_inr'] = df['monthly_rent_inr'].apply(clean_currency)
    df['deposit_inr'] = df['deposit_inr'].apply(clean_currency)
    
    # 2. Normalize localities
    df['locality'] = df['locality'].apply(normalize_locality)
    
    # 3. Handle categorical missing values
    df['food_option'] = df['food_option'].fillna('Not available').astype(str).str.strip()
    df['wifi'] = df['wifi'].fillna('No').astype(str).str.strip().str.capitalize()
    df['ac'] = df['ac'].fillna('No').astype(str).str.strip().str.capitalize()
    df['bathroom_type'] = df['bathroom_type'].fillna('Shared').astype(str).str.strip().str.capitalize()
    df['room_type'] = df['room_type'].fillna('Double Sharing').astype(str).str.strip()
    
    # 4. Impute missing numerical values
    # For rating_demo: fillna with median rating
    median_rating = round(df['rating_demo'].dropna().median(), 1)
    df['rating_demo'] = df['rating_demo'].fillna(median_rating)
    
    # For review count: fillna with 0
    if 'review_count_demo' in df.columns:
        df['review_count_demo'] = df['review_count_demo'].fillna(0).astype(int)
        
    # For deposit_inr: calculate median deposit by locality & room_type, or 2.5 * rent fallback
    group_deposit = df.groupby(['locality', 'room_type'])['deposit_inr'].transform('median')
    df['deposit_inr'] = df['deposit_inr'].fillna(group_deposit)
    # If still NaN, fallback to 2.5 * monthly_rent_inr
    df['deposit_inr'] = df['deposit_inr'].fillna(df['monthly_rent_inr'] * 2.5)
    
    # Calculate deposit-to-rent ratio
    df['deposit_to_rent_ratio'] = (df['deposit_inr'] / df['monthly_rent_inr']).round(2)
    
    # 5. Amenity parsing & multi-hot flags
    df['amenities'] = df['amenities'].fillna('')
    for amenity in KNOWN_AMENITIES:
        col_name = 'amenity_' + amenity.lower().replace(' ', '_')
        # Check case-insensitive presence in amenities string
        pattern = re.escape(amenity.lower())
        df[col_name] = df['amenities'].str.lower().apply(
            lambda x: 1 if re.search(pattern, x) else 0
        )
        
    # Compute total amenity count
    amenity_cols = [col for col in df.columns if col.startswith('amenity_')]
    df['amenity_count'] = df[amenity_cols].sum(axis=1)
    
    summary = {
        'initial_rows': initial_shape[0],
        'final_rows': len(df),
        'unique_localities': df['locality'].nunique(),
        'localities_list': sorted(df['locality'].unique().tolist()),
        'median_rent': float(df['monthly_rent_inr'].median()),
        'mean_rent': float(df['monthly_rent_inr'].mean()),
        'min_rent': float(df['monthly_rent_inr'].min()),
        'max_rent': float(df['monthly_rent_inr'].max()),
        'median_deposit': float(df['deposit_inr'].median()),
        'mean_deposit_ratio': float(df['deposit_to_rent_ratio'].mean())
    }
    
    return df, summary

if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    raw = pd.read_csv('C:/Users/navya/.gemini/antigravity/scratch/bengaluru-pg-safety-intelligence/data/pg_listings.csv')
    cleaned, sm = clean_dataset(raw)
    print("Dataset cleaned successfully!")
    print(f"Shape: {cleaned.shape}")
    print(f"Localities: {sm['unique_localities']}")
    print(f"Rent range: INR {sm['min_rent']:.0f} - INR {sm['max_rent']:.0f} (Median: INR {sm['median_rent']:.0f})")
    print(f"Mean deposit ratio: {sm['mean_deposit_ratio']:.2f}x")
