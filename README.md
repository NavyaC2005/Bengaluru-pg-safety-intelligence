# PG Safety and Price Intelligence for Bengaluru

An end-to-end Data Science and Full-Stack Machine Learning project designed to support individuals comparing Paying Guest (PG) accommodations across Bengaluru. It models rent variations, benchmarks expected prices with Scikit-learn regressors, flags listings requiring physical verification using transparent rule-based indicators, and ranks options according to user preferences and budget.

---

## 📌 Deliverables Overview

This repository implements both pathways specified in the project plan:

1. **Option A — Data Science Pipeline & Jupyter Notebook (`notebooks/`)**:
   - Ingestion and cleaning of 400 demonstration records.
   - Exploratory Data Analysis (EDA) and 5 high-resolution visualizations.
   - Feature engineering pipeline using `ColumnTransformer` with `OneHotEncoder`.
   - Comparative evaluation between **Linear Regression** (baseline) and **Random Forest Regressor** on held-out test data.
   - Residual error inspection across Bengaluru localities and room sharing types.
   - Explainable safety verification engine and multi-criteria recommendation demo.

2. **Option B — Full-Stack Web Application (`web/`)**:
   - **Backend**: Python with Flask, RESTful endpoints (`/api/recommend`, `/api/predict`, `/api/verify`).
   - **Frontend**: Clean, responsive user interface (HTML5, modern CSS3 with Plus Jakarta Sans typography, and vanilla JavaScript).
   - **Interactive Views**:
     - **Market Overview (`/`)**: Locality rent benchmarks and interactive analytics.
     - **PG Finder (`/find`)**: Filter listings by budget slider, locality, room type, and facilities with composite match scoring (0–100) and price assessment tags.
     - **Rent Estimator (`/estimate`)**: Live estimation tool using the trained Random Forest model with $\pm 12\%$ confidence bounds.
     - **Safety Verifier (`/verify`)**: Listing audit tool scanning for elevated deposit ratios, advance-token demands, and attribute contradictions.
     - **Methodology & Ethics (`/methodology`)**: Scientific workflow documentation and responsible disclosure boundaries.

---

## 📁 Repository Structure

```text
bengaluru-pg-safety-intelligence/
├── data/
│   └── pg_listings.csv               # 400-row demonstration dataset
├── notebooks/
│   ├── pg_safety_and_price_intelligence.ipynb # Full Jupyter notebook
│   └── charts/                       # Generated EDA & evaluation charts
│       ├── rent_by_locality.png
│       ├── rent_by_room_type.png
│       ├── deposit_to_rent_ratio.png
│       ├── amenities_frequency.png
│       └── model_comparison.png
├── src/
│   ├── data_cleaner.py               # Currency parsing, locality normalization, imputation
│   ├── feature_pipeline.py           # Preprocessing & ColumnTransformer pipeline
│   ├── model_trainer.py              # Supervised model training & evaluation
│   ├── warning_engine.py             # Rule-based safety verification engine
│   ├── recommender.py                # Multi-criteria filtering & preference ranking
│   ├── generate_charts.py            # Automated chart generator
│   └── create_notebook.py            # Script that built the notebook
├── models/
│   ├── rent_prediction_model.joblib  # Serialized production model pipeline
│   └── model_metrics.json            # Train and test MAE, RMSE, R² scores
├── web/
│   ├── app.py                        # Flask server & REST API
│   ├── templates/                    # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── find.html
│   │   ├── estimate.html
│   │   ├── verify.html
│   │   └── listing_detail.html
│   └── static/
│       ├── css/styles.css            # Responsive custom design system
│       ├── js/main.js                # Dynamic AJAX and filter logic
│       └── charts/                   # Web-optimized analytics charts
├── tests/
│   └── test_app.py                   # 8-point Flask integration test suite
├── run_pipeline.py                   # Automated end-to-end pipeline runner
└── README.md                         # Project documentation
```

---

## 🚀 Quickstart & Execution

### 1. Run Complete Automated Pipeline
To clean the data, generate all visual charts, train models, and execute the demonstration queries:
```bash
python run_pipeline.py
```

### 2. Run Flask Web Application
To launch the interactive web portal locally:
```bash
python web/app.py
```
Then open your browser at `http://127.0.0.1:5000`.

### 3. Run Integration Tests
To verify all web routes and API endpoints:
```bash
python tests/test_app.py
```

---

## 📊 Machine Learning Performance Comparison

Models were trained on an 80% split (320 records) and benchmarked on a strictly held-out 20% test split (80 records). Deposit was deliberately excluded from input features to avoid post-outcome target leakage.

| Algorithm | Role | Test MAE | Test RMSE | Test $R^2$ Score |
| :--- | :--- | :--- | :--- | :--- |
| **Linear Regression** | Interpretable Linear Baseline | ₹2,335.28 | ₹3,076.31 | 0.6829 |
| **Random Forest Regressor** | Non-Linear Comparison Model | ₹2,440.80 | ₹3,389.13 | 0.6152 |

---

## 🛡️ Transparent Warning Indicators & Ethical Limits

As emphasized in Section 9 of the project plan:
> **Ethical Boundary:** We do not classify any listing as a confirmed scam solely because rent or deposit is high, a rating is low, or a rule is triggered. Such factors may have innocent explanations.

The system surfaces transparent checks to prompt independent manual verification:
1. **Elevated Deposit Ratio**: Deposit $\ge 4.5\times$ monthly rent (Bengaluru market average is 1.5x–3.0x).
2. **Advance Payment Prompt**: Demanding gate pass fees or token transfers prior to physical in-person inspection.
3. **Attribute Discrepancies**: Contradictions between textual claims (e.g. AC) and structured data.
4. **Template Descriptions**: Repeated bulk listing templates.
5. **Price Anomalies**: Unusually low rent relative to locality benchmarks (potential bait-and-switch checks).

---

## 🧪 Section 13 Example Demonstration Walkthrough

**User Query**:
- Locality: **BTM Layout**
- Room Type: **Double Sharing**
- Wi-Fi: **Required**
- Maximum Budget: **₹12,000**

**System Output**:
- Filters matching listings within budget.
- Calls trained ML model for predicted rent (~₹12,800).
- Flags listing `DEMO-PG-0296` (Rent: ₹12,300, Deposit: ₹49,000, Deposit ratio: 4.0x) with label `Review Carefully` due to elevated deposit ratio.
- Advises user to verify deposit refund clauses and inspect physical property before transferring funds.
