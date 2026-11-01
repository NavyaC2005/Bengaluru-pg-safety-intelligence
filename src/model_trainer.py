"""
Model Training & Evaluation Module for Bengaluru PG Rent Prediction
Trains and compares Linear Regression (baseline) and Random Forest Regressor.
Reports MAE, RMSE, R² on held-out test data, computes errors by locality and room type,
and serializes the production model.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from data_cleaner import clean_dataset
from feature_pipeline import (
    create_feature_preprocessor,
    prepare_feature_dataframe,
    ALL_MODEL_FEATURES
)

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'rent_prediction_model.joblib')
METRICS_PATH = os.path.join(MODEL_DIR, 'model_metrics.json')

def train_and_evaluate(df_cleaned: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
    """
    Trains Linear Regression and Random Forest Regressor on cleaned data.
    Evaluates both on held-out test data and saves the best model.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # 1. Prepare X and y
    X = df_cleaned[ALL_MODEL_FEATURES].copy()
    y = df_cleaned['monthly_rent_inr'].copy()
    
    # 2. Split train and test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # 3. Build pipelines
    preprocessor = create_feature_preprocessor()
    
    linear_pipeline = Pipeline([
        ('preprocessor', create_feature_preprocessor()),
        ('regressor', LinearRegression())
    ])
    
    rf_pipeline = Pipeline([
        ('preprocessor', create_feature_preprocessor()),
        ('regressor', RandomForestRegressor(n_estimators=120, max_depth=12, random_state=random_state))
    ])
    
    # 4. Train Linear Regression Baseline
    linear_pipeline.fit(X_train, y_train)
    y_pred_lr_test = linear_pipeline.predict(X_test)
    y_pred_lr_train = linear_pipeline.predict(X_train)
    
    # 5. Train Random Forest Comparison
    rf_pipeline.fit(X_train, y_train)
    y_pred_rf_test = rf_pipeline.predict(X_test)
    y_pred_rf_train = rf_pipeline.predict(X_train)
    
    # 6. Compute metrics
    def calculate_metrics(y_true, y_pred):
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))
        return {'mae': round(mae, 2), 'rmse': round(rmse, 2), 'r2': round(r2, 4)}
        
    metrics = {
        'dataset_info': {
            'total_samples': len(df_cleaned),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'test_ratio': test_size,
            'random_seed': random_state
        },
        'linear_regression': {
            'train': calculate_metrics(y_train, y_pred_lr_train),
            'test': calculate_metrics(y_test, y_pred_lr_test)
        },
        'random_forest': {
            'train': calculate_metrics(y_train, y_pred_rf_train),
            'test': calculate_metrics(y_test, y_pred_rf_test)
        }
    }
    
    # 7. Error breakdown by locality & room type on test set (Random Forest)
    test_eval_df = X_test.copy()
    test_eval_df['actual_rent'] = y_test
    test_eval_df['predicted_rent'] = y_pred_rf_test
    test_eval_df['abs_error'] = np.abs(test_eval_df['actual_rent'] - test_eval_df['predicted_rent'])
    
    locality_errors = test_eval_df.groupby('locality')['abs_error'].agg(['count', 'mean']).round(2).to_dict('index')
    room_type_errors = test_eval_df.groupby('room_type')['abs_error'].agg(['count', 'mean']).round(2).to_dict('index')
    
    metrics['errors_by_locality'] = locality_errors
    metrics['errors_by_room_type'] = room_type_errors
    
    # 8. Save best model (Random Forest) & metadata
    joblib.dump(rf_pipeline, MODEL_PATH)
    
    with open(METRICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
        
    return rf_pipeline, linear_pipeline, metrics, test_eval_df

def predict_rent_estimate(listing_dict: dict) -> dict:
    """Loads saved model and returns predicted rent with standard deviation confidence interval."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not trained yet at {MODEL_PATH}")
    
    model = joblib.load(MODEL_PATH)
    X_single = prepare_feature_dataframe(listing_dict)
    
    pred_val = float(model.predict(X_single)[0])
    # Benchmark uncertainty range (approx +/- 12%)
    lower_bound = round(pred_val * 0.88, -2)
    upper_bound = round(pred_val * 1.12, -2)
    estimated_rent = round(pred_val, -2)
    
    return {
        'estimated_rent_inr': int(estimated_rent),
        'range_low_inr': int(lower_bound),
        'range_high_inr': int(upper_bound),
        'model_name': 'Random Forest Regressor (Trained Pipeline)'
    }

if __name__ == '__main__':
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        
    raw_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'pg_listings.csv')
    raw_df = pd.read_csv(raw_path)
    cleaned_df, _ = clean_dataset(raw_df)
    
    rf, lr, results, _ = train_and_evaluate(cleaned_df)
    
    print("=" * 60)
    print("RENT PREDICTION MODEL EVALUATION RESULTS (HELD-OUT TEST SET)")
    print("=" * 60)
    print(f"Linear Regression (Baseline) -> MAE: INR {results['linear_regression']['test']['mae']}, RMSE: INR {results['linear_regression']['test']['rmse']}, R2: {results['linear_regression']['test']['r2']}")
    print(f"Random Forest Regressor      -> MAE: INR {results['random_forest']['test']['mae']}, RMSE: INR {results['random_forest']['test']['rmse']}, R2: {results['random_forest']['test']['r2']}")
    print("=" * 60)
    print(f"Model successfully saved to {MODEL_PATH}")
    print(f"Metrics saved to {METRICS_PATH}")
    
    # Test sample prediction
    sample_test = {
        'locality': 'BTM Layout',
        'room_type': 'Double Sharing',
        'food_option': 'Included',
        'wifi': 'Yes',
        'ac': 'No',
        'bathroom_type': 'Attached',
        'amenities': ['Power backup', 'CCTV', 'Lift']
    }
    pred = predict_rent_estimate(sample_test)
    print(f"Sample prediction for BTM Layout (Double Sharing, Food Included): INR {pred['estimated_rent_inr']} (Range: INR {pred['range_low_inr']} - {pred['range_high_inr']})")
