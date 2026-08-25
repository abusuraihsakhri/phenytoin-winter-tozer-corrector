#!/usr/bin/env python3
"""
Phenytoin Winter-Tozer Correction Calculator

Corrects measured total phenytoin levels for hypoalbuminemia and renal impairment.
Implements Michaelis-Menten kinetics for dose adjustment.

Key formulas:
- Normal albumin: Corrected = Measured / ((0.25 * albumin) + 0.1)
- Renal impairment (CrCl <10): Corrected = Measured / ((0.1 * albumin) + 0.1)
- Michaelis-Menten: Css = (Vmax * Dose/tau) / (Km + Dose/tau)
- Steady state estimation from two levels
- Loading dose calculation

Therapeutic range: 10-20 mg/L (total), 1-2 mg/L (free)

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional, Tuple


# ============================================================================
# Constants
# ============================================================================

# Therapeutic ranges
TOTAL_THERAPEUTIC_LOW = 10.0   # mg/L
TOTAL_THERAPEUTIC_HIGH = 20.0  # mg/L
FREE_THERAPEUTIC_LOW = 1.0     # mg/L
FREE_THERAPEUTIC_HIGH = 2.0    # mg/L

# Normal albumin range
ALBUMIN_NORMAL_LOW = 3.5       # g/dL
ALBUMIN_NORMAL_HIGH = 5.0      # g/dL

# Population Michaelis-Menten parameters
DEFAULT_VMAX = 7.0             # mg/kg/day (population average)
DEFAULT_KM = 4.0               # mg/L (population average)

# Phenytoin properties
PHENYTOIN_HALF_LIFE_NORMAL = 22.0  # hours (average)
PHENYTOIN_F = 0.95                  # Oral bioavailability


# ============================================================================
# Winter-Tozer Correction
# ============================================================================

def correct_phenytoin_normal(
    measured_phenytoin_mg_l: float,
    albumin_g_dl: float
) -> Dict[str, Any]:
    """
    Correct phenytoin level for hypoalbuminemia (normal renal function).
    
    Winter-Tozer equation:
    Corrected = Measured / ((0.25 * albumin) + 0.1)
    
    Args:
        measured_phenytoin_mg_l: Measured total phenytoin in mg/L
        albumin_g_dl: Serum albumin in g/dL
        
    Returns:
        Dictionary with corrected phenytoin and interpretation
    """
    if albumin_g_dl <= 0:
        raise ValueError("Albumin must be positive")
    if measured_phenytoin_mg_l < 0:
        raise ValueError("Measured phenytoin must be non-negative")
    
    binding_fraction = (0.25 * albumin_g_dl) + 0.1
    corrected = measured_phenytoin_mg_l / binding_fraction
    
    return {
        "measured_phenytoin_mg_l": measured_phenytoin_mg_l,
        "albumin_g_dl": albumin_g_dl,
        "binding_fraction": round(binding_fraction, 3),
        "corrected_phenytoin_mg_l": round(corrected, 1),
        "correction_formula": "Measured / ((0.25 * albumin) + 0.1)",
        "renal_adjustment": False
    }


def correct_phenytoin_renal(
    measured_phenytoin_mg_l: float,
    albumin_g_dl: float
) -> Dict[str, Any]:
    """
    Correct phenytoin level for hypoalbuminemia with renal impairment.
    
    Modified Winter-Tozer for ESRD/CrCl <10:
    Corrected = Measured / ((0.1 * albumin) + 0.1)
    
    Args:
        measured_phenytoin_mg_l: Measured total phenytoin in mg/L
        albumin_g_dl: Serum albumin in g/dL
        
    Returns:
        Dictionary with corrected phenytoin and interpretation
    """
    if albumin_g_dl <= 0:
        raise ValueError("Albumin must be positive")
    if measured_phenytoin_mg_l < 0:
        raise ValueError("Measured phenytoin must be non-negative")
    
    binding_fraction = (0.1 * albumin_g_dl) + 0.1
    corrected = measured_phenytoin_mg_l / binding_fraction
    
    return {
        "measured_phenytoin_mg_l": measured_phenytoin_mg_l,
        "albumin_g_dl": albumin_g_dl,
        "binding_fraction": round(binding_fraction, 3),
        "corrected_phenytoin_mg_l": round(corrected, 1),
        "correction_formula": "Measured / ((0.1 * albumin) + 0.1)",
        "renal_adjustment": True
    }


def correct_phenytoin(
    measured_phenytoin_mg_l: float,
    albumin_g_dl: float,
    crcl_ml_min: Optional[float] = None
) -> Dict[str, Any]:
    """
    Correct phenytoin level using appropriate Winter-Tozer equation.
    
    Automatically selects renal-adjusted formula if CrCl < 10 mL/min.
    
    Args:
        measured_phenytoin_mg_l: Measured total phenytoin in mg/L
        albumin_g_dl: Serum albumin in g/dL
        crcl_ml_min: Creatinine clearance in mL/min (optional)
        
    Returns:
        Dictionary with corrected phenytoin and interpretation
    """
    if crcl_ml_min is not None and crcl_ml_min < 10:
        result = correct_phenytoin_renal(measured_phenytoin_mg_l, albumin_g_dl)
    else:
        result = correct_phenytoin_normal(measured_phenytoin_mg_l, albumin_g_dl)
    
    # Add interpretation
    corrected = result["corrected_phenytoin_mg_l"]
    result["interpretation"] = interpret_phenytoin(corrected)
    
    return result


def interpret_phenytoin(corrected_mg_l: float) -> Dict[str, Any]:
    """
    Interpret corrected phenytoin concentration.
    
    Args:
        corrected_mg_l: Corrected total phenytoin in mg/L
        
    Returns:
        Dictionary with interpretation
    """
    if corrected_mg_l < 0:
        raise ValueError("Corrected phenytoin must be non-negative")
    
    if corrected_mg_l < TOTAL_THERAPEUTIC_LOW:
        status = "SUBTHERAPEUTIC"
        recommendation = "Increase dose. Phenytoin below therapeutic range (10-20 mg/L)."
        risk = "Seizure breakthrough risk"
    elif corrected_mg_l <= TOTAL_THERAPEUTIC_HIGH:
        status = "THERAPEUTIC"
        recommendation = "Within therapeutic range. Continue current regimen."
        risk = "Within therapeutic range"
    elif corrected_mg_l <= 30.0:
        status = "MILDLY_TOXIC"
        recommendation = "Reduce dose. Monitor for toxicity symptoms (nystagmus, ataxia)."
        risk = "Early toxicity signs possible"
    elif corrected_mg_l <= 40.0:
        status = "MODERATELY_TOXIC"
        recommendation = "Hold dose and reduce. Significant toxicity risk."
        risk = "Nystagmus, ataxia, slurred speech likely"
    else:
        status = "SEVERELY_TOXIC"
        recommendation = "Hold phenytoin. Monitor closely. Consider ICU admission."
        risk = "Severe CNS toxicity, cardiac arrhythmia risk"
    
    return {
        "corrected_phenytoin_mg_l": corrected_mg_l,
        "status": status,
        "recommendation": recommendation,
        "risk": risk,
        "therapeutic_range": "10-20 mg/L (total)"
    }


# ============================================================================
# Michaelis-Menten Kinetics
# ============================================================================

def calculate_steady_state_mm(
    daily_dose_mg: float,
    vmax_mg_per_day: float = DEFAULT_VMAX * 70,
    km_mg_l: float = DEFAULT_KM
) -> Dict[str, Any]:
    """
    Calculate steady-state phenytoin concentration using Michaelis-Menten kinetics.
    
    Css = (Vmax * Dose_rate) / (Km + Dose_rate)
    where Dose_rate = daily_dose_mg (since Vmax is in mg/day)
    
    More precisely:
    Css = (Vmax * D/tau) / (Km + D/tau)
    For once-daily: Css = (Vmax * daily_dose) / (Km * F * 24 + daily_dose)
    Simplified: Css = (Vmax * daily_dose) / (Km + daily_dose)
    
    Args:
        daily_dose_mg: Daily phenytoin dose in mg
        vmax_mg_per_day: Maximum metabolism rate in mg/day (default 490 mg/day for 70kg)
        km_mg_l: Michaelis constant in mg/L (default 4.0)
        
    Returns:
        Dictionary with steady-state concentration
    """
    if daily_dose_mg <= 0:
        raise ValueError("Daily dose must be positive")
    if vmax_mg_per_day <= 0:
        raise ValueError("Vmax must be positive")
    if km_mg_l <= 0:
        raise ValueError("Km must be positive")
    
    # Css = (Vmax * Dose_rate) / (Km + Dose_rate)
    # For phenytoin: Css = (Vmax * daily_dose) / (Km * bioavailability + daily_dose)
    # Simplified: Css = (Vmax * daily_dose) / (Km + daily_dose)
    css = (vmax_mg_per_day * daily_dose_mg) / (km_mg_l * PHENYTOIN_F * 1000 + daily_dose_mg)
    
    # Alternative formulation (more standard):
    # Css (mg/L) = (Vmax (mg/day) * Dose (mg/day)) / (Km (mg/L) * F * 1000 + Dose (mg/day))
    # This gives Css in mg/L
    
    return {
        "daily_dose_mg": daily_dose_mg,
        "vmax_mg_per_day": vmax_mg_per_day,
        "km_mg_l": km_mg_l,
        "bioavailability": PHENYTOIN_F,
        "predicted_css_mg_l": round(css, 1),
        "interpretation": interpret_phenytoin(css),
        "saturation_warning": css > 15 and daily_dose_mg > 300,
        "notes": "Michaelis-Menten kinetics: small dose increases can cause large concentration changes near saturation."
    }


def estimate_vmax_km_from_two_levels(
    dose1_mg_day: float,
    css1_mg_l: float,
    dose2_mg_day: float,
    css2_mg_l: float
) -> Dict[str, Any]:
    """
    Estimate individual Vmax and Km from two steady-state dose/concentration pairs.
    
    Using two Michaelis-Menten equations:
    Css1 = (Vmax * D1) / (Km + D1)
    Css2 = (Vmax * D2) / (Km + D2)
    
    Solving:
    Km = (D1 * Css2 - D2 * Css1) / (Css1 - Css2)  [when Css1 != Css2]
    Vmax = Css1 * (Km + D1) / D1
    
    Args:
        dose1_mg_day: First daily dose in mg
        css1_mg_l: Steady-state concentration at first dose in mg/L
        dose2_mg_day: Second daily dose in mg
        css2_mg_l: Steady-state concentration at second dose in mg/L
        
    Returns:
        Dictionary with estimated Vmax and Km
    """
    if dose1_mg_day <= 0 or dose2_mg_day <= 0:
        raise ValueError("Both doses must be positive")
    if css1_mg_l <= 0 or css2_mg_l <= 0:
        raise ValueError("Both concentrations must be positive")
    if abs(css1_mg_l - css2_mg_l) < 0.01:
        raise ValueError("Concentrations must differ for parameter estimation")
    
    # Solve for Km using correct derivation:
    # Css = (Vmax * D) / (Km + D)  =>  Km = D1*D2*(Css1-Css2) / (Css2*D1 - Css1*D2)
    numerator = dose1_mg_day * dose2_mg_day * (css1_mg_l - css2_mg_l)
    denominator = css2_mg_l * dose1_mg_day - css1_mg_l * dose2_mg_day
    
    if abs(denominator) < 0.001:
        raise ValueError("Data is inconsistent - cannot estimate parameters.")
    
    km = numerator / denominator
    
    if km <= 0:
        raise ValueError("Calculated Km is non-positive. Data may be inconsistent.")
    
    # Solve for Vmax
    vmax = css1_mg_l * (km + dose1_mg_day) / dose1_mg_day
    
    return {
        "estimated_vmax_mg_per_day": round(vmax, 1),
        "estimated_km_mg_l": round(km, 2),
        "input_data": {
            "dose1_mg_day": dose1_mg_day,
            "css1_mg_l": css1_mg_l,
            "dose2_mg_day": dose2_mg_day,
            "css2_mg_l": css2_mg_l
        },
        "notes": "Individual Vmax/Km estimated from two steady-state levels. Use for personalized dosing."
    }


def predict_dose_for_target_css(
    target_css_mg_l: float,
    vmax_mg_per_day: float = DEFAULT_VMAX * 70,
    km_mg_l: float = DEFAULT_KM
) -> Dict[str, Any]:
    """
    Predict daily dose needed to achieve target steady-state concentration.
    
    Rearranging Michaelis-Menten:
    Dose = (Css * Vmax) / (Vmax - Css)  [when Css < Vmax]
    
    More precisely with Km:
    Dose = (Css * Km) / (Vmax - Css)  [simplified]
    Dose = (target_css * km * vmax) / (vmax - target_css)  [corrected]
    
    Args:
        target_css_mg_l: Target steady-state concentration in mg/L
        vmax_mg_per_day: Maximum metabolism rate in mg/day
        km_mg_l: Michaelis constant in mg/L
        
    Returns:
        Dictionary with predicted dose
    """
    if target_css_mg_l <= 0:
        raise ValueError("Target concentration must be positive")
    if target_css_mg_l >= vmax_mg_per_day / (km_mg_l + 1):
        raise ValueError("Target concentration too high - may not be achievable safely")
    
    # From Css = (Vmax * D) / (Km + D), solve for D:
    # D = (Css * Km) / (Vmax - Css)
    # But we need to account for units properly
    # Css (mg/L) = (Vmax (mg/day) * D (mg/day)) / (Km (mg/L) * F * 1000 + D (mg/day))
    # Solve for D:
    # Css * (Km * F * 1000 + D) = Vmax * D
    # Css * Km * F * 1000 + Css * D = Vmax * D
    # Css * Km * F * 1000 = D * (Vmax - Css)
    # D = (Css * Km * F * 1000) / (Vmax - Css)
    
    denominator = vmax_mg_per_day - target_css_mg_l
    if denominator <= 0:
        raise ValueError("Target concentration exceeds Vmax - not achievable")
    
    daily_dose = (target_css_mg_l * km_mg_l * PHENYTOIN_F * 1000) / denominator
    
    return {
        "target_css_mg_l": target_css_mg_l,
        "vmax_mg_per_day": vmax_mg_per_day,
        "km_mg_l": km_mg_l,
        "predicted_daily_dose_mg": round(daily_dose, 0),
        "predicted_daily_dose_mg_per_kg": round(daily_dose / 70, 1),
        "notes": "Dose prediction based on Michaelis-Menten kinetics. Monitor levels after adjustment."
    }


def calculate_loading_dose(
    target_concentration_mg_l: float,
    vd_liters_per_kg: float = 0.7,
    weight_kg: float = 70.0,
    bioavailability: float = PHENYTOIN_F
) -> Dict[str, Any]:
    """
    Calculate phenytoin loading dose.
    
    LD = (Vd * target_concentration * weight) / F
    
    Args:
        target_concentration_mg_l: Target concentration in mg/L
        vd_liters_per_kg: Volume of distribution in L/kg (default 0.7)
        weight_kg: Patient weight in kg
        bioavailability: Oral bioavailability
        
    Returns:
        Dictionary with loading dose
    """
    if target_concentration_mg_l <= 0:
        raise ValueError("Target concentration must be positive")
    if weight_kg <= 0:
        raise ValueError("Weight must be positive")
    
    vd_total = vd_liters_per_kg * weight_kg
    ld_mg = (vd_total * target_concentration_mg_l) / bioavailability
    
    # Round to nearest 50mg for practical dosing
    ld_rounded = round(ld_mg / 50) * 50
    
    # Max single oral dose: 400mg (to avoid cardiac effects)
    # Max IV rate: 50mg/min
    max_oral = 400
    num_oral_doses = math.ceil(ld_rounded / max_oral)
    
    return {
        "target_concentration_mg_l": target_concentration_mg_l,
        "vd_liters": round(vd_total, 1),
        "weight_kg": weight_kg,
        "loading_dose_mg": ld_rounded,
        "loading_dose_mg_per_kg": round(ld_rounded / weight_kg, 1),
        "oral_dosing": {
            "max_single_dose_mg": max_oral,
            "number_of_doses": num_oral_doses,
            "dose_per_administration_mg": min(ld_rounded, max_oral),
            "note": "Give divided doses, max 400mg per dose orally"
        },
        "iv_dosing": {
            "max_rate_mg_per_min": 50,
            "infusion_time_minutes": round(ld_rounded / 50, 0),
            "note": "Max IV rate 50mg/min with cardiac monitoring"
        },
        "notes": "Loading dose for acute situations. Monitor levels 2-4 hours post-oral dose."
    }


def saturation_kinetics_warning(
    current_dose_mg: float,
    proposed_increase_mg: float,
    current_css_mg_l: Optional[float] = None
) -> Dict[str, Any]:
    """
    Warn about phenytoin saturation kinetics.
    
    Near saturation, small dose increases cause disproportionate concentration rises.
    Rule of thumb: at 300mg/day, a 10% dose increase can cause 50-100% concentration increase.
    
    Args:
        current_dose_mg: Current daily dose in mg
        proposed_increase_mg: Proposed dose increase in mg
        current_css_mg_l: Current steady-state concentration (optional)
        
    Returns:
        Dictionary with saturation warnings
    """
    warnings = []
    risk_level = "LOW"
    
    if current_dose_mg >= 300:
        warnings.append("Current dose >=300mg/day: approaching saturation kinetics zone.")
        risk_level = "MODERATE"
    
    if current_dose_mg >= 400:
        warnings.append("Current dose >=400mg/day: high saturation risk. Small increases may cause toxicity.")
        risk_level = "HIGH"
    
    if proposed_increase_mg > 100:
        warnings.append(f"Proposed increase of {proposed_increase_mg}mg is large. Consider smaller increments (25-50mg).")
        risk_level = "HIGH"
    
    if current_css_mg_l and current_css_mg_l > 15:
        warnings.append(f"Current level {current_css_mg_l} mg/L is near upper therapeutic limit.")
        risk_level = "HIGH"
    
    # Estimate concentration increase using M-M kinetics
    vmax = DEFAULT_VMAX * 70  # 490 mg/day
    km = DEFAULT_KM  # 4 mg/L
    
    if current_dose_mg > 0:
        css_current = (vmax * current_dose_mg) / (km * PHENYTOIN_F * 1000 + current_dose_mg)
        css_new = (vmax * (current_dose_mg + proposed_increase_mg)) / (km * PHENYTOIN_F * 1000 + current_dose_mg + proposed_increase_mg)
        
        pct_dose_change = (proposed_increase_mg / current_dose_mg) * 100
        pct_css_change = ((css_new - css_current) / css_current) * 100 if css_current > 0 else 0
        
        if pct_css_change > pct_dose_change * 2:
            warnings.append(
                f"Non-linear kinetics: {pct_dose_change:.0f}% dose increase may cause "
                f"~{pct_css_change:.0f}% concentration increase."
            )
    
    return {
        "current_dose_mg": current_dose_mg,
        "proposed_increase_mg": proposed_increase_mg,
        "risk_level": risk_level,
        "warnings": warnings,
        "recommendation": "Increase dose in small increments (25-50mg). Wait 5-7 half-lives (7-14 days) before reassessing.",
        "saturation_notes": "Phenytoin follows Michaelis-Menten (zero-order) kinetics at therapeutic doses."
    }


# ============================================================================
# Full Assessment
# ============================================================================

def full_phenytoin_assessment(
    measured_phenytoin_mg_l: float,
    albumin_g_dl: float,
    crcl_ml_min: Optional[float] = None,
    daily_dose_mg: Optional[float] = None,
    weight_kg: float = 70.0,
    vmax_mg_per_day: Optional[float] = None,
    km_mg_l: Optional[float] = None
) -> Dict[str, Any]:
    """
    Complete phenytoin assessment with correction and dosing guidance.
    
    Args:
        measured_phenytoin_mg_l: Measured total phenytoin in mg/L
        albumin_g_dl: Serum albumin in g/dL
        crcl_ml_min: Creatinine clearance in mL/min
        daily_dose_mg: Current daily dose in mg
        weight_kg: Patient weight in kg
        vmax_mg_per_day: Individual Vmax if known
        km_mg_l: Individual Km if known
        
    Returns:
        Complete assessment dictionary
    """
    # Step 1: Correct phenytoin for albumin
    correction = correct_phenytoin(measured_phenytoin_mg_l, albumin_g_dl, crcl_ml_min)
    corrected = correction["corrected_phenytoin_mg_l"]
    
    # Step 2: Interpret corrected level
    interp = interpret_phenytoin(corrected)
    
    # Step 3: Estimate free phenytoin (approximately 10% of total)
    free_phenytoin = round(corrected * 0.1, 1)
    
    # Step 4: If dose provided, predict steady-state
    ss_prediction = None
    if daily_dose_mg:
        v = vmax_mg_per_day if vmax_mg_per_day else DEFAULT_VMAX * weight_kg
        k = km_mg_l if km_mg_l else DEFAULT_KM
        ss_prediction = calculate_steady_state_mm(daily_dose_mg, v, k)
    
    # Step 5: Loading dose if subtherapeutic
    loading = None
    if corrected < TOTAL_THERAPEUTIC_LOW:
        loading = calculate_loading_dose(TOTAL_THERAPEUTIC_HIGH, weight_kg=weight_kg)
    
    # Step 6: Saturation warning if dose provided
    saturation = None
    if daily_dose_mg:
        saturation = saturation_kinetics_warning(daily_dose_mg, 50, corrected)
    
    return {
        "correction": correction,
        "corrected_phenytoin_mg_l": corrected,
        "estimated_free_phenytoin_mg_l": free_phenytoin,
        "interpretation": interp,
        "steady_state_prediction": ss_prediction,
        "loading_dose": loading,
        "saturation_warning": saturation,
        "disclaimer": "FOR EDUCATIONAL/RESEARCH USE ONLY. Not a substitute for clinical pharmacist review."
    }


def main(argv=None):
    """CLI entry point for phenytoin correction calculator."""
    parser = argparse.ArgumentParser(
        prog="phenytoin-correct",
        description="Phenytoin Winter-Tozer Correction Calculator"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # --- Correct command ---
    correct_parser = subparsers.add_parser("correct", help="Correct phenytoin for albumin")
    correct_parser.add_argument("--phenytoin", type=float, required=True, help="Measured phenytoin mg/L")
    correct_parser.add_argument("--albumin", type=float, required=True, help="Serum albumin g/dL")
    correct_parser.add_argument("--crcl", type=float, help="CrCl mL/min (if <10, uses renal formula)")
    
    # --- Steady-state command ---
    ss_parser = subparsers.add_parser("steady-state", help="Predict steady-state from dose")
    ss_parser.add_argument("--dose", type=float, required=True, help="Daily dose in mg")
    ss_parser.add_argument("--vmax", type=float, help="Vmax mg/day (default population)")
    ss_parser.add_argument("--km", type=float, help="Km mg/L (default 4.0)")
    
    # --- Estimate Vmax/Km command ---
    est_parser = subparsers.add_parser("estimate-params", help="Estimate Vmax/Km from two levels")
    est_parser.add_argument("--dose1", type=float, required=True, help="First daily dose mg")
    est_parser.add_argument("--css1", type=float, required=True, help="Css at first dose mg/L")
    est_parser.add_argument("--dose2", type=float, required=True, help="Second daily dose mg")
    est_parser.add_argument("--css2", type=float, required=True, help="Css at second dose mg/L")
    
    # --- Loading dose command ---
    ld_parser = subparsers.add_parser("loading-dose", help="Calculate loading dose")
    ld_parser.add_argument("--target", type=float, required=True, help="Target concentration mg/L")
    ld_parser.add_argument("--weight", type=float, default=70.0, help="Weight in kg (default 70)")
    
    # --- Assess command ---
    assess_parser = subparsers.add_parser("assess", help="Full assessment")
    assess_parser.add_argument("--phenytoin", type=float, required=True, help="Measured phenytoin mg/L")
    assess_parser.add_argument("--albumin", type=float, required=True, help="Serum albumin g/dL")
    assess_parser.add_argument("--crcl", type=float, help="CrCl mL/min")
    assess_parser.add_argument("--dose", type=float, help="Current daily dose mg")
    assess_parser.add_argument("--weight", type=float, default=70.0, help="Weight kg")
    
    args = parser.parse_args(argv)
    
    if args.command == "correct":
        result = correct_phenytoin(args.phenytoin, args.albumin, args.crcl)
        print(json.dumps(result, indent=2))
    
    elif args.command == "steady-state":
        v = args.vmax if args.vmax else DEFAULT_VMAX * 70
        k = args.km if args.km else DEFAULT_KM
        result = calculate_steady_state_mm(args.dose, v, k)
        print(json.dumps(result, indent=2))
    
    elif args.command == "estimate-params":
        result = estimate_vmax_km_from_two_levels(args.dose1, args.css1, args.dose2, args.css2)
        print(json.dumps(result, indent=2))
    
    elif args.command == "loading-dose":
        result = calculate_loading_dose(args.target, weight_kg=args.weight)
        print(json.dumps(result, indent=2))
    
    elif args.command == "assess":
        result = full_phenytoin_assessment(
            args.phenytoin, args.albumin, args.crcl, args.dose, args.weight
        )
        print(json.dumps(result, indent=2))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
