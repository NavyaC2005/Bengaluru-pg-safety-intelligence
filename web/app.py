"""
Bengaluru PG Safety & Price Intelligence - Flask Web Application
Provides interactive endpoints for PG recommendations, ML rent estimation,
and listing safety verification with transparent explainable flags.
"""

import os
import sys
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, abort

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from data_cleaner import clean_dataset, LOCALITY_MAPPING, KNOWN_AMENITIES
from recommender import PGRecommender
from model_trainer import predict_rent_estimate, METRICS_PATH
from warning_engine import evaluate_listing_safety

app = Flask(__name__)

# Data & Recommender Initialization
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'pg_listings.csv'))
raw_df = pd.read_csv(DATA_PATH)
cleaned_df, cleaning_summary = clean_dataset(raw_df)
recommender = PGRecommender(cleaned_df)

# Load model evaluation metrics if present
model_metrics = {}
if os.path.exists(METRICS_PATH):
    try:
        with open(METRICS_PATH, 'r', encoding='utf-8') as f:
            model_metrics = json.load(f)
    except Exception:
        pass

@app.context_processor
def inject_global_data():
    return {
        'all_localities': sorted(cleaned_df['locality'].unique().tolist()),
        'all_room_types': ['Single', 'Double Sharing', 'Triple Sharing', 'Four Sharing'],
        'all_food_options': ['Included', 'Available at extra cost', 'Not available'],
        'known_amenities': KNOWN_AMENITIES,
        'cleaning_summary': cleaning_summary,
        'model_metrics': model_metrics
    }

@app.route('/')
def home():
    """Home / Market Intelligence Dashboard."""
    # Compute locality stats
    loc_stats = cleaned_df.groupby('locality').agg(
        listing_count=('monthly_rent_inr', 'count'),
        median_rent=('monthly_rent_inr', 'median'),
        min_rent=('monthly_rent_inr', 'min'),
        max_rent=('monthly_rent_inr', 'max'),
        median_deposit=('deposit_inr', 'median')
    ).reset_index().sort_values(by='median_rent', ascending=False)
    
    # Calculate warning counts
    warning_counts = cleaned_df['rule_based_warning_label'].value_counts().to_dict()
    
    return render_template(
        'index.html',
        loc_stats=loc_stats.to_dict('records'),
        warning_counts=warning_counts,
        total_listings=len(cleaned_df)
    )

@app.route('/find')
def find_pg():
    """PG Finder & Recommendation page."""
    # Default search query
    default_query = {
        'budget': 15000,
        'locality': 'Any',
        'room_type': 'Any',
        'wifi_required': False,
        'ac_required': False,
        'food_option': 'Any',
        'preferred_amenities': []
    }
    initial_results = recommender.recommend(default_query, top_k=15)
    return render_template('find.html', initial_results=initial_results)

@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    """REST API endpoint returning filtered & scored PG listings."""
    try:
        data = request.get_json() or {}
        budget = float(data.get('budget', 15000))
        locality = str(data.get('locality', 'Any'))
        room_type = str(data.get('room_type', 'Any'))
        wifi_req = bool(data.get('wifi_required', False))
        ac_req = bool(data.get('ac_required', False))
        food_opt = str(data.get('food_option', 'Any'))
        amenities = data.get('preferred_amenities', [])
        
        pref = {
            'budget': budget,
            'locality': locality,
            'room_type': room_type,
            'wifi_required': wifi_req,
            'ac_required': ac_req,
            'food_option': food_opt,
            'preferred_amenities': amenities
        }
        
        results = recommender.recommend(pref, top_k=20)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e), 'total_matches': 0, 'recommendations': []}), 400

@app.route('/estimate')
def estimate_page():
    """Interactive Rent Estimator page."""
    return render_template('estimate.html')

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """REST API predicting rent with confidence range using Random Forest."""
    try:
        data = request.get_json() or {}
        pred_result = predict_rent_estimate(data)
        return jsonify(pred_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/verify')
def verify_page():
    """Listing Safety & Verification page."""
    return render_template('verify.html')

@app.route('/api/verify', methods=['POST'])
def api_verify():
    """REST API running rule-based transparency checks."""
    try:
        data = request.get_json() or {}
        # If rent is provided, also run model to check for price anomaly
        predicted_rent = None
        if data.get('locality') and data.get('room_type'):
            try:
                pred = predict_rent_estimate(data)
                predicted_rent = pred.get('estimated_rent_inr')
            except Exception:
                pass
                
        eval_result = evaluate_listing_safety(data, predicted_rent)
        eval_result['predicted_rent_benchmark'] = predicted_rent
        return jsonify(eval_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/listing/<listing_id>')
def listing_details(listing_id):
    """Detailed view for a specific PG listing."""
    matches = cleaned_df[cleaned_df['listing_id'] == listing_id]
    if matches.empty:
        abort(404)
        
    listing = matches.iloc[0].to_dict()
    # Model estimation
    predicted_rent = None
    try:
        pred = predict_rent_estimate(listing)
        predicted_rent = pred.get('estimated_rent_inr')
    except Exception:
        pass
        
    safety = evaluate_listing_safety(listing, predicted_rent)
    return render_template('listing_detail.html', listing=listing, predicted_rent=predicted_rent, safety=safety)

if __name__ == '__main__':
    # Run locally on port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
