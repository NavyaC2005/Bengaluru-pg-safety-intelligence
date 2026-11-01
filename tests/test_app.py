"""
Unit & Integration Tests for Flask Application and API Endpoints
Verifies that all views render properly and APIs return expected JSON.
"""

import sys
import os
import json

# Add web and src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web')))

from app import app

def test_flask_application():
    client = app.test_client()
    
    print("Testing Web Application Routes & Endpoints:")
    
    # 1. Test Home Route
    res_home = client.get('/')
    assert res_home.status_code == 200, f"Home failed: {res_home.status_code}"
    assert b"Bengaluru PG Price & Safety Intelligence" in res_home.data
    print(" [PASS] GET / (Market Overview) -> Status 200")
    
    # 2. Test Find Route
    res_find = client.get('/find')
    assert res_find.status_code == 200, f"Find failed: {res_find.status_code}"
    assert b"Find & Compare PG Accommodations" in res_find.data
    print(" [PASS] GET /find (PG Finder) -> Status 200")
    
    # 3. Test Estimate Route
    res_est = client.get('/estimate')
    assert res_est.status_code == 200, f"Estimate failed: {res_est.status_code}"
    assert b"Machine Learning Rent Estimator" in res_est.data
    print(" [PASS] GET /estimate (Rent Estimator) -> Status 200")
    
    # 4. Test Verify Route
    res_ver = client.get('/verify')
    assert res_ver.status_code == 200, f"Verify failed: {res_ver.status_code}"
    assert b"Listing Safety & Transparency Verifier" in res_ver.data
    print(" [PASS] GET /verify (Safety Verifier) -> Status 200")
    
    # 5. Test Listing Detail Route
    res_detail = client.get('/listing/DEMO-PG-0001')
    assert res_detail.status_code == 200, f"Listing detail failed: {res_detail.status_code}"
    assert b"DEMO-PG-0001" in res_detail.data
    print(" [PASS] GET /listing/DEMO-PG-0001 (Detail View) -> Status 200")
    
    # 6. Test API Recommend Endpoint
    demo_query = {
        'budget': 14000,
        'locality': 'BTM Layout',
        'room_type': 'Double Sharing',
        'wifi_required': True
    }
    res_api_rec = client.post(
        '/api/recommend',
        data=json.dumps(demo_query),
        content_type='application/json'
    )
    assert res_api_rec.status_code == 200, f"API recommend failed: {res_api_rec.status_code}"
    data_rec = res_api_rec.get_json()
    assert 'recommendations' in data_rec
    print(f" [PASS] POST /api/recommend -> Status 200, Found {data_rec['total_matches']} matches")
    
    # 7. Test API Predict Endpoint
    predict_query = {
        'locality': 'Whitefield',
        'room_type': 'Single',
        'food_option': 'Included',
        'wifi': 'Yes',
        'ac': 'Yes',
        'bathroom_type': 'Attached',
        'amenities': ['Lift', 'Gym', 'CCTV']
    }
    res_api_pred = client.post(
        '/api/predict',
        data=json.dumps(predict_query),
        content_type='application/json'
    )
    assert res_api_pred.status_code == 200, f"API predict failed: {res_api_pred.status_code}"
    data_pred = res_api_pred.get_json()
    assert 'estimated_rent_inr' in data_pred
    print(f" [PASS] POST /api/predict -> Status 200, Estimated Rent: INR {data_pred['estimated_rent_inr']:,}")
    
    # 8. Test API Verify Endpoint
    verify_query = {
        'monthly_rent_inr': 10000,
        'deposit_inr': 70000,
        'locality': 'Koramangala',
        'room_type': 'Double Sharing',
        'pay_before_visit_indicator': 1,
        'listing_description_demo': 'Advance token required.'
    }
    res_api_ver = client.post(
        '/api/verify',
        data=json.dumps(verify_query),
        content_type='application/json'
    )
    assert res_api_ver.status_code == 200, f"API verify failed: {res_api_ver.status_code}"
    data_ver = res_api_ver.get_json()
    assert data_ver['warning_count'] >= 2
    print(f" [PASS] POST /api/verify -> Status 200, Label: {data_ver['rule_based_warning_label']}")
    
    print("\nALL FLASK INTEGRATION TESTS PASSED (8/8)!")

if __name__ == '__main__':
    test_flask_application()
