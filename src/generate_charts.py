"""
Exploratory Data Analysis & Model Visualization Generator
Generates high-resolution EDA and evaluation charts for notebook and web dashboard.
"""

import os
import sys

# Configure headless matplotlib & writable cache directory
os.environ['MPLCONFIGDIR'] = os.path.join(os.path.dirname(__file__), '..', '.mpl_cache')
os.makedirs(os.environ['MPLCONFIGDIR'], exist_ok=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from data_cleaner import clean_dataset

# Setup aesthetics
sns.set_theme(style='whitegrid', font_scale=1.05)
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8

CHARTS_DIRS = [
    os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'charts'),
    os.path.join(os.path.dirname(__file__), '..', 'web', 'static', 'charts')
]

for d in CHARTS_DIRS:
    os.makedirs(d, exist_ok=True)

def save_fig_to_all(fig, filename):
    for d in CHARTS_DIRS:
        fig.savefig(os.path.join(d, filename), dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {filename}")

def generate_all_charts():
    raw_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'pg_listings.csv')
    raw_df = pd.read_csv(raw_path)
    df, summary = clean_dataset(raw_df)
    
    # 1. Rent by Locality (Horizontal Boxplot sorted by median)
    loc_order = df.groupby('locality')['monthly_rent_inr'].median().sort_values(ascending=True).index
    fig, ax = plt.subplots(figsize=(10, 7))
    palette = sns.color_palette("mako", len(loc_order))
    sns.boxplot(
        data=df, y='locality', x='monthly_rent_inr',
        order=loc_order, palette=palette, ax=ax,
        fliersize=3, linewidth=1.2
    )
    ax.set_title('Bengaluru PG Monthly Rent Distribution by Locality (INR)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Monthly Rent (INR)', fontsize=12)
    ax.set_ylabel('Locality', fontsize=12)
    ax.xaxis.set_major_formatter('{x:,.0f}')
    save_fig_to_all(fig, 'rent_by_locality.png')
    
    # 2. Rent by Room Type
    room_order = ['Single', 'Double Sharing', 'Triple Sharing', 'Four Sharing']
    fig, ax = plt.subplots(figsize=(8, 5.5))
    palette_room = sns.color_palette("crest", len(room_order))
    sns.boxplot(
        data=df, x='room_type', y='monthly_rent_inr',
        order=room_order, palette=palette_room, ax=ax,
        linewidth=1.2
    )
    ax.set_title('Monthly Rent by Room Sharing Type', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Room Type', fontsize=12)
    ax.set_ylabel('Monthly Rent (INR)', fontsize=12)
    ax.yaxis.set_major_formatter('{x:,.0f}')
    save_fig_to_all(fig, 'rent_by_room_type.png')
    
    # 3. Deposit to Rent Ratio Distribution
    fig, ax = plt.subplots(figsize=(8.5, 5))
    sns.histplot(
        df['deposit_to_rent_ratio'], kde=True, bins=25,
        color='#0284c7', ax=ax, edgecolor='white'
    )
    ax.axvline(x=4.5, color='#ef4444', linestyle='--', linewidth=2, label='High-Deposit Warning Threshold (4.5x)')
    ax.axvspan(1.0, 3.0, alpha=0.15, color='#10b981', label='Standard Market Range (1x - 3x)')
    ax.set_title('Deposit-to-Rent Ratio Distribution & Anomaly Boundary', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Deposit / Monthly Rent (Ratio)', fontsize=12)
    ax.set_ylabel('Number of Listings', fontsize=12)
    ax.legend(frameon=True, facecolor='white', loc='upper right')
    save_fig_to_all(fig, 'deposit_to_rent_ratio.png')
    
    # 4. Amenities Frequency
    amenity_cols = [c for c in df.columns if c.startswith('amenity_') and c != 'amenity_count']
    amenity_counts = df[amenity_cols].sum().sort_values(ascending=True)
    labels = [c.replace('amenity_', '').replace('_', ' ').title() for c in amenity_counts.index]
    
    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(labels, amenity_counts.values, color='#4f46e5', edgecolor='none', height=0.65)
    ax.set_title('Prevalence of Amenities Across 400 PG Listings', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Number of Listings Offering Amenity', fontsize=12)
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 3, bar.get_y() + bar.get_height()/2, f'{int(w)} ({w/len(df)*100:.0f}%)',
                va='center', fontsize=9.5, color='#334155')
    ax.set_xlim(0, len(df) + 30)
    save_fig_to_all(fig, 'amenities_frequency.png')
    
    # 5. Model Evaluation Metrics Comparison
    metrics_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'model_metrics.json')
    if os.path.exists(metrics_path):
        import json
        with open(metrics_path, 'r') as f:
            metrics_data = json.load(f)
            
        lr_test = metrics_data['linear_regression']['test']
        rf_test = metrics_data['random_forest']['test']
        
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        
        # MAE
        axes[0].bar(['Linear Reg', 'Random Forest'], [lr_test['mae'], rf_test['mae']], color=['#0284c7', '#0d9488'])
        axes[0].set_title('MAE (Lower is Better)', fontweight='bold')
        axes[0].set_ylabel('INR')
        for i, v in enumerate([lr_test['mae'], rf_test['mae']]):
            axes[0].text(i, v + 40, f'₹{v:,.0f}', ha='center', fontweight='bold', fontsize=10)
            
        # RMSE
        axes[1].bar(['Linear Reg', 'Random Forest'], [lr_test['rmse'], rf_test['rmse']], color=['#0284c7', '#0d9488'])
        axes[1].set_title('RMSE (Lower is Better)', fontweight='bold')
        axes[1].set_ylabel('INR')
        for i, v in enumerate([lr_test['rmse'], rf_test['rmse']]):
            axes[1].text(i, v + 50, f'₹{v:,.0f}', ha='center', fontweight='bold', fontsize=10)
            
        # R2
        axes[2].bar(['Linear Reg', 'Random Forest'], [lr_test['r2'], rf_test['r2']], color=['#0284c7', '#0d9488'])
        axes[2].set_title('R² Variance Explained (Higher is Better)', fontweight='bold')
        axes[2].set_ylim(0, 1.0)
        for i, v in enumerate([lr_test['r2'], rf_test['r2']]):
            axes[2].text(i, v + 0.03, f'{v:.3f}', ha='center', fontweight='bold', fontsize=10)
            
        plt.suptitle('Held-Out Test Set Performance Comparison', fontsize=13, fontweight='bold', y=1.05)
        plt.tight_layout()
        save_fig_to_all(fig, 'model_comparison.png')

if __name__ == '__main__':
    generate_all_charts()
    print("All charts generated successfully!")
