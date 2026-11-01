"""
Multi-Criteria PG Recommendation Engine for Bengaluru
Filters listings by budget, locality, room type, and facilities, then ranks matches
by composite preference fit, estimated market value, and safety profile.
"""

import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, List, Any

from warning_engine import evaluate_listing_safety
from feature_pipeline import prepare_feature_dataframe

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'rent_prediction_model.joblib')

class PGRecommender:
    def __init__(self, cleaned_df: pd.DataFrame, model_path: str = MODEL_PATH):
        self.df = cleaned_df.copy()
        self.model = None
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
            except Exception as e:
                print(f"Warning: Could not load model from {model_path}: {e}")
                
    def recommend(self, preferences: Dict[str, Any], top_k: int = 10) -> Dict[str, Any]:
        """
        Filters and ranks PG listings according to user preferences.
        """
        budget = float(preferences.get('budget', 15000))
        locality = str(preferences.get('locality', 'Any')).strip()
        room_type = str(preferences.get('room_type', 'Any')).strip()
        wifi_req = bool(preferences.get('wifi_required', False))
        ac_req = bool(preferences.get('ac_required', False))
        food_req = str(preferences.get('food_option', 'Any')).strip()
        preferred_amenities = preferences.get('preferred_amenities', [])
        
        candidates = self.df.copy()
        
        # 1. Filter by Locality
        if locality and locality.lower() not in ['any', 'all']:
            candidates = candidates[candidates['locality'].str.lower() == locality.lower()]
            
        # 2. Filter by Room Type
        if room_type and room_type.lower() not in ['any', 'all']:
            candidates = candidates[candidates['room_type'].str.lower() == room_type.lower()]
            
        # 3. Filter by WiFi
        if wifi_req:
            candidates = candidates[candidates['wifi'].str.lower() == 'yes']
            
        # 4. Filter by AC
        if ac_req:
            candidates = candidates[candidates['ac'].str.lower() == 'yes']
            
        # 5. Filter by Food Option
        if food_req and food_req.lower() not in ['any', 'all']:
            candidates = candidates[candidates['food_option'].str.lower() == food_req.lower()]
            
        # 6. Filter by Budget (with 10% flexible buffer, but prioritizing strictly <= budget)
        max_allowed_rent = budget * 1.10
        candidates = candidates[candidates['monthly_rent_inr'] <= max_allowed_rent]
        
        if len(candidates) == 0:
            return {
                'total_matches': 0,
                'recommendations': [],
                'filter_summary': {
                    'budget': budget,
                    'locality': locality,
                    'room_type': room_type
                },
                'message': "No PG listings matched all strict criteria. Try expanding budget or setting locality to 'Any'."
            }
            
        # 7. Score each candidate
        scored_listings = []
        for _, row in candidates.iterrows():
            row_dict = row.to_dict()
            rent = float(row_dict.get('monthly_rent_inr', 0))
            
            # Predict market rent if model is available
            predicted_rent = None
            if self.model is not None:
                try:
                    feat_df = prepare_feature_dataframe(row_dict)
                    predicted_rent = float(self.model.predict(feat_df)[0])
                except Exception:
                    predicted_rent = None
                    
            # Warning & safety evaluation
            safety_eval = evaluate_listing_safety(row_dict, predicted_rent)
            
            # Score Components:
            # A) Budget Fit (0 - 30 pts)
            if rent <= budget:
                # Bonus for saving money up to budget
                budget_score = 20.0 + (10.0 * (budget - rent) / max(1.0, budget))
            else:
                # Slight penalty for 10% buffer
                budget_score = max(5.0, 20.0 - (15.0 * (rent - budget) / (budget * 0.10)))
                
            # B) Amenity Match (0 - 40 pts)
            if preferred_amenities:
                matched_amenities = 0
                for am in preferred_amenities:
                    col_name = 'amenity_' + am.lower().replace(' ', '_')
                    if row_dict.get(col_name) == 1:
                        matched_amenities += 1
                amenity_score = (matched_amenities / len(preferred_amenities)) * 40.0
            else:
                # If no specific amenities requested, score based on total amenities count
                total_amenities = row_dict.get('amenity_count', 0)
                amenity_score = min(40.0, (total_amenities / 8.0) * 40.0)
                
            # C) Rating Score (0 - 20 pts)
            rating = float(row_dict.get('rating_demo', 3.5))
            rating_score = (rating / 5.0) * 20.0
            
            # D) Safety Profile (0 - 10 pts)
            w_count = safety_eval['warning_count']
            if w_count == 0:
                safety_score = 10.0
            elif w_count == 1:
                safety_score = 6.0
            else:
                safety_score = 2.0
                
            total_score = round(budget_score + amenity_score + rating_score + safety_score, 1)
            
            # Difference from predicted rent
            price_delta = None
            price_tag = "Market rate"
            if predicted_rent:
                delta = rent - predicted_rent
                price_delta = int(delta)
                if delta <= -1500:
                    price_tag = f"INR {abs(int(delta)):,} below market estimate (Good value)"
                elif delta >= 1500:
                    price_tag = f"INR {int(delta):,} above market estimate"
                else:
                    price_tag = "Fair market price"
                    
            listing_summary = {
                'listing_id': row_dict.get('listing_id'),
                'locality': row_dict.get('locality'),
                'room_type': row_dict.get('room_type'),
                'monthly_rent_inr': int(rent),
                'deposit_inr': int(row_dict.get('deposit_inr', 0)),
                'deposit_to_rent_ratio': float(row_dict.get('deposit_to_rent_ratio', 0)),
                'food_option': row_dict.get('food_option'),
                'wifi': row_dict.get('wifi'),
                'ac': row_dict.get('ac'),
                'bathroom_type': row_dict.get('bathroom_type'),
                'amenities': row_dict.get('amenities', ''),
                'rating_demo': rating,
                'review_count_demo': int(row_dict.get('review_count_demo', 0)),
                'listing_description_demo': row_dict.get('listing_description_demo', ''),
                'match_score': total_score,
                'predicted_rent_inr': int(predicted_rent) if predicted_rent else None,
                'price_tag': price_tag,
                'price_delta_inr': price_delta,
                'safety': safety_eval
            }
            scored_listings.append(listing_summary)
            
        # 8. Sort descending by match score
        scored_listings.sort(key=lambda x: x['match_score'], reverse=True)
        top_recommendations = scored_listings[:top_k]
        
        return {
            'total_matches': len(scored_listings),
            'top_k': len(top_recommendations),
            'recommendations': top_recommendations,
            'user_preferences': preferences
        }

if __name__ == '__main__':
    from data_cleaner import clean_dataset
    raw = pd.read_csv('C:/Users/navya/.gemini/antigravity/scratch/bengaluru-pg-safety-intelligence/data/pg_listings.csv')
    df_clean, _ = clean_dataset(raw)
    
    recommender = PGRecommender(df_clean)
    demo_pref = {
        'locality': 'BTM Layout',
        'room_type': 'Double Sharing',
        'wifi_required': True,
        'budget': 14000,
        'preferred_amenities': ['Power backup', 'Lift']
    }
    
    res = recommender.recommend(demo_pref, top_k=3)
    print(f"Total Matches: {res['total_matches']}")
    for i, r in enumerate(res['recommendations'], 1):
        print(f"#{i} [{r['listing_id']}] {r['locality']} | {r['room_type']} | Rent: INR {r['monthly_rent_inr']} (Score: {r['match_score']}/100)")
        print(f"   Safety Status: {r['safety']['rule_based_warning_label']} (Warnings: {r['safety']['warning_count']})")
        print(f"   Price vs Estimate: {r['price_tag']}")
