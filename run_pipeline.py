"""
Complete End-to-End Pipeline Runner
Executes data cleaning, chart generation, ML training & evaluation, safety checks,
and sample recommendation queries in a single automated run.
"""

import os
import sys

# Windows UTF-8 stdout fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
from data_cleaner import clean_dataset
from generate_charts import generate_all_charts
from model_trainer import train_and_evaluate, predict_rent_estimate
from warning_engine import evaluate_listing_safety
from recommender import PGRecommender

def main():
    print("=" * 70)
    print(" BENGALURU PG SAFETY & PRICE INTELLIGENCE PIPELINE")
    print("=" * 70)
    
    # 1. Clean Data
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'pg_listings.csv')
    print(f"\n[1/5] Ingesting and cleaning raw data from: {data_path}")
    raw_df = pd.read_csv(data_path)
    cleaned_df, clean_summary = clean_dataset(raw_df)
    print(f" -> Processed {clean_summary['final_rows']} listings across {clean_summary['unique_localities']} Bengaluru localities.")
    print(f" -> Rent Range: INR {clean_summary['min_rent']:,.0f} - INR {clean_summary['max_rent']:,.0f} (Median: INR {clean_summary['median_rent']:,.0f})")
    print(f" -> Mean Deposit-to-Rent Ratio: {clean_summary['mean_deposit_ratio']:.2f}x")
    
    # 2. Generate EDA Visualizations
    print("\n[2/5] Generating exploratory analysis and model evaluation charts...")
    generate_all_charts()
    print(" -> Charts saved to 'notebooks/charts/' and 'web/static/charts/'.")
    
    # 3. Model Training & Evaluation
    print("\n[3/5] Training supervised rent prediction models (Linear Regression vs Random Forest)...")
    rf_pipe, lr_pipe, metrics, test_eval_df = train_and_evaluate(cleaned_df)
    lr_t = metrics['linear_regression']['test']
    rf_t = metrics['random_forest']['test']
    print(" +-------------------------------------+---------------+---------------+----------+")
    print(" | Model                               | Test MAE (INR)| Test RMSE(INR)| Test R2  |")
    print(" +-------------------------------------+---------------+---------------+----------+")
    print(f" | Linear Regression (Baseline)        | INR {lr_t['mae']:<9,.2f}| INR {lr_t['rmse']:<9,.2f}| {lr_t['r2']:<8.4f} |")
    print(f" | Random Forest Regressor (Trained)   | INR {rf_t['mae']:<9,.2f}| INR {rf_t['rmse']:<9,.2f}| {rf_t['r2']:<8.4f} |")
    print(" +-------------------------------------+---------------+---------------+----------+")
    
    # 4. Warning Indicators Check
    print("\n[4/5] Testing transparent rule-based safety verification engine...")
    test_listing = {
        'locality': 'Koramangala',
        'monthly_rent_inr': 11000,
        'deposit_inr': 75000,
        'room_type': 'Double Sharing',
        'pay_before_visit_indicator': 1,
        'listing_description_demo': 'Double sharing room. Advance visiting token required before viewing.'
    }
    safety_res = evaluate_listing_safety(test_listing, predicted_rent=13500)
    print(f" -> Sample Alert Status: {safety_res['rule_based_warning_label']} ({safety_res['warning_count']} warnings)")
    for w in safety_res['warnings']:
        print(f"    * [{w['severity']}] {w['title']}: {w['message'][:85]}...")
        
    # 5. Recommendation Demonstration (Section 13)
    print("\n[5/5] Running Section 13 Demonstration:")
    print(" -> Criteria: BTM Layout | Double Sharing | Wi-Fi Required | Budget: INR 12,000")
    recommender = PGRecommender(cleaned_df)
    demo_res = recommender.recommend({
        'locality': 'BTM Layout',
        'room_type': 'Double Sharing',
        'wifi_required': True,
        'budget': 12000
    }, top_k=3)
    print(f" -> Found {demo_res['total_matches']} matching PG(s):")
    for i, r in enumerate(demo_res['recommendations'], 1):
        print(f"    #{i} [{r['listing_id']}] Rent: INR {r['monthly_rent_inr']:,} | Deposit: INR {r['deposit_inr']:,} | Match Score: {r['match_score']}/100")
        print(f"       Price Assessment: {r['price_tag']} | Safety: {r['safety']['rule_based_warning_label']}")
        
    print("\n" + "=" * 70)
    print(" ALL PIPELINE STEPS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    main()
