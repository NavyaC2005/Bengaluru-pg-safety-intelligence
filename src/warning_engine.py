"""
Transparent Safety & Verification Engine for Bengaluru PG Listings
Implements rule-based, explainable warning indicators designed to prompt manual verification,
respecting the ethical limits outlined in the project specification.
"""

import re
from typing import Dict, List, Any

# Known suspicious keywords in listings demanding payment before visit
PAY_BEFORE_VISIT_KEYWORDS = [
    'pay before visit', 'token before visit', 'gate pass fee', 'visiting fee',
    'advance token', 'registration fee for visit', 'pay first', 'booking fee before seeing',
    'refundable visiting pass'
]

def check_deposit_ratio(monthly_rent: float, deposit: float) -> (bool, str):
    """
    Checks if the deposit-to-rent ratio is unusually high.
    Bengaluru norm for PGs is typically 1.5x - 3x rent.
    """
    if not monthly_rent or monthly_rent <= 0 or not deposit:
        return False, ""
    
    ratio = deposit / monthly_rent
    if ratio >= 4.5:
        return True, (
            f"High Deposit Alert: Deposit is {ratio:.1f}x the monthly rent "
            f"(Bengaluru PG typical range is 1.5x to 3x). "
            "Ensure deposit refund conditions, notice period, and deduction clauses are explicitly defined in a signed agreement."
        )
    return False, ""

def check_pay_before_visit(description: str, flag_val: Any = None) -> (bool, str):
    """
    Checks if a listing demands payment or fees prior to an in-person physical inspection.
    """
    if flag_val in [1, '1', True, 'Yes']:
        return True, (
            "Advance Payment Prompt: Listing flags payment or token required before physical viewing. "
            "CRITICAL: Never transfer money or 'visitor pass' charges prior to meeting management and inspecting the room."
        )
    
    desc_lower = str(description).lower()
    for kw in PAY_BEFORE_VISIT_KEYWORDS:
        if kw in desc_lower:
            return True, (
                f"Advance Payment Prompt: Found '{kw}' in listing description. "
                "CRITICAL: Never pay token or gate charges without physically visiting the PG."
            )
    return False, ""

def check_inconsistencies(listing: dict) -> (bool, str):
    """
    Checks for contradictory information between description and structured attributes.
    """
    if listing.get('inconsistent_details_indicator') in [1, '1', True]:
        return True, (
            "Inconsistent Listing Attributes: Listing contains contradictory specifications. "
            "Verify actual room sharing, bathroom type, and included utilities directly with the manager."
        )
    
    desc = str(listing.get('listing_description_demo', '')).lower()
    ac_field = str(listing.get('ac', 'No')).lower()
    
    # Contradiction: says "with ac" in description but AC is "No"
    if 'ac' in desc and 'non-ac' not in desc and 'no ac' not in desc:
        if ac_field in ['no', '0', 'false']:
            return True, (
                "Feature Discrepancy: Description mentions AC, but structured details mark AC as 'No'. "
                "Confirm whether electricity / AC usage entails additional charges."
            )
            
    return False, ""

def check_duplicate_template(description: str, flag_val: Any = None) -> (bool, str):
    """
    Checks for generic or duplicate listing template descriptions.
    """
    if flag_val in [1, '1', True]:
        return True, (
            "Template Description: Description matches generic or repeated text templates. "
            "Ask management for recent photos/video and inspect in person."
        )
    return False, ""

def check_price_anomaly(monthly_rent: float, predicted_rent: float = None) -> (bool, str):
    """
    Flags listings that appear unrealistically cheap for the locality and room type (potential bait-and-switch).
    """
    if not predicted_rent or not monthly_rent or monthly_rent <= 0:
        return False, ""
    
    if monthly_rent < (predicted_rent * 0.55):
        diff = int(predicted_rent - monthly_rent)
        return True, (
            f"Price Anomaly (Bait Check): Rent (INR {int(monthly_rent):,}) is over 45% below the estimated market benchmark "
            f"(~INR {int(predicted_rent):,}). "
            "Confirm there are no hidden food, electricity, maintenance, or shared utility costs."
        )
    return False, ""

def evaluate_listing_safety(listing: dict, predicted_rent: float = None) -> Dict[str, Any]:
    """
    Main evaluation pipeline that inspects listing details against explainable verification rules.
    Returns warnings list, composite score, risk badge, and tenant advice.
    """
    warnings = []
    
    # 1. High deposit check
    rent = float(listing.get('monthly_rent_inr') or 0)
    deposit = float(listing.get('deposit_inr') or 0)
    high_dep_flag = listing.get('high_deposit_indicator')
    
    is_high_dep, dep_msg = check_deposit_ratio(rent, deposit)
    if is_high_dep or high_dep_flag in [1, '1', True]:
        warnings.append({
            'code': 'HIGH_DEPOSIT',
            'severity': 'MEDIUM',
            'title': 'Elevated Deposit Ratio',
            'message': dep_msg if dep_msg else "Deposit is significantly higher than standard monthly rent ratios."
        })
        
    # 2. Pay before visit check
    pay_flag = listing.get('pay_before_visit_indicator')
    desc = listing.get('listing_description_demo', '')
    is_pay, pay_msg = check_pay_before_visit(desc, pay_flag)
    if is_pay:
        warnings.append({
            'code': 'PAY_BEFORE_VISIT',
            'severity': 'HIGH',
            'title': 'Advance Payment Prompt',
            'message': pay_msg
        })
        
    # 3. Inconsistencies check
    is_inconsistent, inc_msg = check_inconsistencies(listing)
    if is_inconsistent:
        warnings.append({
            'code': 'INCONSISTENT_DETAILS',
            'severity': 'MEDIUM',
            'title': 'Attribute Discrepancy',
            'message': inc_msg
        })
        
    # 4. Duplicate template check
    dup_flag = listing.get('duplicate_description_indicator')
    is_dup, dup_msg = check_duplicate_template(desc, dup_flag)
    if is_dup:
        warnings.append({
            'code': 'TEMPLATE_DESCRIPTION',
            'severity': 'LOW',
            'title': 'Generic Description',
            'message': dup_msg
        })
        
    # 5. Price anomaly / bait check
    if predicted_rent and rent > 0:
        is_cheap, cheap_msg = check_price_anomaly(rent, predicted_rent)
        if is_cheap:
            warnings.append({
                'code': 'UNUSUALLY_LOW_RENT',
                'severity': 'MEDIUM',
                'title': 'Unusually Low Price Benchmark',
                'message': cheap_msg
            })
            
    warning_count = len(warnings)
    if warning_count == 0:
        label = "No Rule-Based Flag"
        badge = "badge-success"
        status_text = "Standard listing. Standard due diligence applies."
    elif warning_count == 1:
        label = "Review Carefully"
        badge = "badge-warning"
        status_text = "Prompt for verification: review specific items noted below."
    else:
        label = "High Verification Prompt"
        badge = "badge-danger"
        status_text = "Multiple review indicators flagged. Thorough in-person verification advised."
        
    checklist = [
        "Schedule an in-person physical viewing during daylight hours.",
        "Demand a written rental agreement with clear notice period & deposit refund terms.",
        "Verify electricity billing (commercial vs domestic meter rate).",
        "Inspect water supply, drinking water filter, Wi-Fi speed, and power backup.",
        "Never transfer security deposit or token money without signed proof of booking."
    ]
    
    return {
        'warning_count': warning_count,
        'rule_based_warning_label': label,
        'badge_class': badge,
        'status_text': status_text,
        'warnings': warnings,
        'verification_checklist': checklist,
        'ethical_disclaimer': (
            "Notice: These indicators are automated decision-support checks designed to highlight listing details "
            "that deserve physical verification. They are NOT certified proof of fraud or scam. "
            "Legitimate PG accommodations may occasionally trigger these checks."
        )
    }

if __name__ == '__main__':
    test_listing = {
        'locality': 'Koramangala',
        'monthly_rent_inr': 12000,
        'deposit_inr': 85000,
        'room_type': 'Double Sharing',
        'pay_before_visit_indicator': 1,
        'listing_description_demo': 'Double Sharing PG with power backup. Please pay 500 advance token before visiting.'
    }
    res = evaluate_listing_safety(test_listing, predicted_rent=14500)
    print("Warning Evaluation Test:")
    print(f"Warning Count: {res['warning_count']} | Label: {res['rule_based_warning_label']}")
    for w in res['warnings']:
        print(f" - [{w['severity']}] {w['title']}: {w['message']}")
