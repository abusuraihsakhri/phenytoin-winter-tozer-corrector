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

def _validate_correction_inputs(measured_phenytoin_mg_l: float, albumin_g_dl: float) -> None:
    """Reject physiologically impossible and non-finite inputs."""
    if not math.isfinite(measured_phenytoin_mg_l) or measured_phenytoin_mg_l < 0:
        raise ValueError("Measured phenytoin must be finite and non-negative")
    if not math.isfinite(albumin_g_dl) or albumin_g_dl <= 0:
        raise ValueError("Albumin must be finite and positive")


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
    _validate_correction_inputs(measured_phenytoin_mg_l, albumin_g_dl)
    
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
    _validate_correction_inputs(measured_phenytoin_mg_l, albumin_g_dl)
    
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
    if crcl_ml_min is not None and (not math.isfinite(crcl_ml_min) or crcl_ml_min < 0):
        raise ValueError("Creatinine clearance must be finite and non-negative")
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
    if not math.isfinite(corrected_mg_l) or corrected_mg_l < 0:
        raise ValueError("Corrected phenytoin must be finite and non-negative")
    
    if corrected_mg_l < TOTAL_THERAPEUTIC_LOW:
        status = "SUBTHERAPEUTIC"
        recommendation = "Below conventional corrected-total range; review timing, adherence, clinical response and measured free concentration before considering dose changes."
        risk = "Seizure breakthrough risk"
    elif corrected_mg_l <= TOTAL_THERAPEUTIC_HIGH:
        status = "THERAPEUTIC"
        recommendation = "Within conventional corrected-total range; interpret with symptoms and measured free concentration where available."
        risk = "Within therapeutic range"
    elif corrected_mg_l <= 30.0:
        status = "MILDLY_TOXIC"
        recommendation = "Above conventional corrected-total range; review symptoms and obtain a measured free concentration."
        risk = "Early toxicity signs possible"
    elif corrected_mg_l <= 40.0:
        status = "MODERATELY_TOXIC"
        recommendation = "Elevated estimate; promptly assess for toxicity and measure free phenytoin."
        risk = "Nystagmus, ataxia, slurred speech likely"
    else:
        status = "SEVERELY_TOXIC"
        recommendation = "Markedly elevated estimate; urgently assess the patient and obtain measured free phenytoin."
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
    """Research-only steady-state model: F * dose = Vmax * Css / (Km + Css).

    Vmax is mg/day; Km and Css are mg/L. Solving gives
    Css = Km * F * dose / (Vmax - F * dose).
    This assumes steady state and population parameters, not an individual prescription.
    """
    if not all(math.isfinite(x) and x > 0 for x in (daily_dose_mg, vmax_mg_per_day, km_mg_l)):
        raise ValueError("Dose, Vmax and Km must be finite and positive")
    input_rate = PHENYTOIN_F * daily_dose_mg
    if input_rate >= vmax_mg_per_day:
        raise ValueError("F * daily dose must be below Vmax; no finite steady state exists")
    css = km_mg_l * input_rate / (vmax_mg_per_day - input_rate)
    return {
        "daily_dose_mg": daily_dose_mg,
        "vmax_mg_per_day": vmax_mg_per_day,
        "km_mg_l": km_mg_l,
        "bioavailability": PHENYTOIN_F,
        "predicted_css_mg_l": round(css, 1),
        "interpretation": interpret_phenytoin(css),
        "saturation_warning": input_rate / vmax_mg_per_day > 0.8,
        "notes": "Research-only population model. Phenytoin has saturable clearance; individual monitoring is essential."
    }

def estimate_vmax_km_from_two_levels(
    dose1_mg_day: float,
    css1_mg_l: float,
    dose2_mg_day: float,
    css2_mg_l: float
) -> Dict[str, Any]:
    """Fit Vmax (mg/day) and Km (mg/L) from two STEADY-STATE dose/level pairs.

    F*D = Vmax*Css/(Km+Css), assuming equal bioavailability for both pairs.
    The inverse fit can be unstable; verify steady state and unchanged interactions.
    """
    vals = (dose1_mg_day, css1_mg_l, dose2_mg_day, css2_mg_l)
    if not all(math.isfinite(x) and x > 0 for x in vals):
        raise ValueError("Both doses and concentrations must be finite and positive")
    if dose1_mg_day == dose2_mg_day or css1_mg_l == css2_mg_l:
        raise ValueError("Two distinct dose and concentration pairs are required")
    input1 = PHENYTOIN_F * dose1_mg_day
    input2 = PHENYTOIN_F * dose2_mg_day
    denominator = input1 / css1_mg_l - input2 / css2_mg_l
    if math.isclose(denominator, 0.0, rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError("Data do not identify a stable Km estimate")
    km = (input2 - input1) / denominator
    vmax = input1 * (km + css1_mg_l) / css1_mg_l
    if not all(math.isfinite(x) and x > 0 for x in (km, vmax)):
        raise ValueError("Pairs are inconsistent with positive Michaelis-Menten parameters")
    if not (vmax > max(input1, input2)):
        raise ValueError("Estimated Vmax must exceed both input rates")
    return {
        "estimated_vmax_mg_per_day": round(vmax, 1),
        "estimated_km_mg_l": round(km, 2),
        "input_data": {
            "dose1_mg_day": dose1_mg_day, "css1_mg_l": css1_mg_l,
            "dose2_mg_day": dose2_mg_day, "css2_mg_l": css2_mg_l
        },
        "notes": "Research-only two-point nonlinear pharmacokinetic fit; not a validated individual dose recommendation."
    }

def predict_dose_for_target_css(
    target_css_mg_l: float,
    vmax_mg_per_day: float = DEFAULT_VMAX * 70,
    km_mg_l: float = DEFAULT_KM
) -> Dict[str, Any]:
    """Invert the research-only steady-state model for an oral daily dose.

    Dose (mg/day) = Vmax * Css / (F * (Km + Css)).
    """
    if not all(math.isfinite(x) and x > 0 for x in (target_css_mg_l, vmax_mg_per_day, km_mg_l)):
        raise ValueError("Target concentration, Vmax and Km must be finite and positive")
    daily_dose = vmax_mg_per_day * target_css_mg_l / (PHENYTOIN_F * (km_mg_l + target_css_mg_l))
    return {
        "target_css_mg_l": target_css_mg_l,
        "vmax_mg_per_day": vmax_mg_per_day,
        "km_mg_l": km_mg_l,
        "predicted_daily_dose_mg": round(daily_dose, 0),
        "predicted_daily_dose_mg_per_kg": round(daily_dose / 70, 1),
        "notes": "Research-only inverse model; not a prescription. Confirm with clinical evaluation and drug levels."
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
    if not math.isfinite(target_concentration_mg_l) or target_concentration_mg_l <= 0:
        raise ValueError("Target concentration must be positive")
    if not math.isfinite(weight_kg) or weight_kg <= 0:
        raise ValueError("Weight must be positive")
    
    if not math.isfinite(vd_liters_per_kg) or vd_liters_per_kg <= 0:
        raise ValueError("Volume of distribution must be finite and positive")
    if not math.isfinite(bioavailability) or not 0 < bioavailability <= 1:
        raise ValueError("Bioavailability must be finite and between 0 and 1")
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
        "notes": "Research-only loading-dose estimate; route, timing, formulation and rate must be clinician-verified."
    }


def saturation_kinetics_warning(
    current_dose_mg: float,
    proposed_increase_mg: float,
    current_css_mg_l: Optional[float] = None
) -> Dict[str, Any]:
    """Flag increases with potentially disproportionate steady-state exposure."""
    if not math.isfinite(current_dose_mg) or current_dose_mg <= 0:
        raise ValueError("Current dose must be finite and positive")
    if not math.isfinite(proposed_increase_mg) or proposed_increase_mg < 0:
        raise ValueError("Proposed increase must be finite and non-negative")
    if current_css_mg_l is not None and (not math.isfinite(current_css_mg_l) or current_css_mg_l < 0):
        raise ValueError("Current concentration must be finite and non-negative")
    warnings = []
    risk_level = "LOW"
    if current_dose_mg >= 300:
        warnings.append("Population-dose thresholds do not establish individual saturation; monitor concentrations.")
        risk_level = "MODERATE"
    if current_dose_mg >= 400 or proposed_increase_mg > 100:
        warnings.append("Large input rate or increase: seek specialist review before changes.")
        risk_level = "HIGH"
    if current_css_mg_l is not None and current_css_mg_l > 15:
        warnings.append("Estimated concentration approaches the conventional upper reference limit.")
        risk_level = "HIGH"
    vmax = DEFAULT_VMAX * 70
    old_input = PHENYTOIN_F * current_dose_mg
    new_input = PHENYTOIN_F * (current_dose_mg + proposed_increase_mg)
    if new_input >= vmax:
        warnings.append("Population model predicts no finite steady state at proposed input rate.")
        risk_level = "HIGH"
    elif old_input < vmax and proposed_increase_mg > 0:
        css_current = DEFAULT_KM * old_input / (vmax - old_input)
        css_new = DEFAULT_KM * new_input / (vmax - new_input)
        pct_dose_change = proposed_increase_mg / current_dose_mg * 100
        pct_css_change = (css_new / css_current - 1) * 100
        if pct_css_change > pct_dose_change * 2:
            warnings.append(
                f"Population model: {pct_dose_change:.0f}% dose increase may raise "
                f"steady-state concentration by {pct_css_change:.0f}%."
            )
            risk_level = "HIGH"
    return {
        "current_dose_mg": current_dose_mg,
        "proposed_increase_mg": proposed_increase_mg,
        "risk_level": risk_level,
        "warnings": warnings,
        "recommendation": "Do not adjust dosing from this model alone; obtain clinical/pharmacist assessment and measured levels.",
        "saturation_notes": "Steady-state concentration increases sharply as F*dose approaches Vmax."
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
    
    # Step 3: Proxy free estimate only; not a measured unbound concentration.
    free_phenytoin = round(corrected * 0.1, 1)
    
    # Step 4: Population model if a dose is provided; not a dosing recommendation
    ss_prediction = None
    if daily_dose_mg is not None:
        if not math.isfinite(weight_kg) or weight_kg <= 0:
            raise ValueError("Weight must be finite and positive")
        v = vmax_mg_per_day if vmax_mg_per_day is not None else DEFAULT_VMAX * weight_kg
        k = km_mg_l if km_mg_l is not None else DEFAULT_KM
        ss_prediction = calculate_steady_state_mm(daily_dose_mg, v, k)
    
    # Step 5: No automatic loading-dose advice from an estimated concentration.
    loading = None
    
    # Step 6: Model saturation warning if dose provided
    saturation = None
    if daily_dose_mg is not None:
        saturation = saturation_kinetics_warning(daily_dose_mg, 50, corrected)
    
    return {
        "correction": correction,
        "corrected_phenytoin_mg_l": corrected,
        "estimated_free_phenytoin_mg_l": free_phenytoin,
        "interpretation": interp,
        "steady_state_prediction": ss_prediction,
        "loading_dose": loading,
        "saturation_warning": saturation,
        "disclaimer": "Research use only. Corrected levels are estimates, not measured free concentrations; dosing requires clinical/pharmacist review."
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

    # --- Audit command ---
    audit_parser = subparsers.add_parser("audit", help="Log an audit event")
    audit_parser.add_argument("--task-id", type=str, required=True, help="Task identifier for the audit event")
    audit_parser.add_argument("--actor", type=str, default="cli", help="Actor initiating the event")
    audit_parser.add_argument("--event-type", type=str, default="CLI_AUDIT_EVENT", help="Type of audit event")

    # --- Chat command ---
    chat_parser = subparsers.add_parser("chat", help="Query the LLM reasoning adapter")
    chat_parser.add_argument("query", nargs="+", help="Query string for the LLM")

    # --- Verify audit command ---
    verify_parser = subparsers.add_parser("verify-audit", help="Verify HMAC-SHA256 audit trail integrity")

    # --- Serve command (FastAPI) ---
    serve_parser = subparsers.add_parser("serve", help="Start FastAPI REST server")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind (default 8000)")

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

    elif args.command == "audit":
        from agents.base import AuditLogger
        entry = AuditLogger.log(
            actor=args.actor,
            actor_tier="cli",
            event_type=args.event_type,
            details={"task_id": args.task_id, "source": "cli"}
        )
        print(json.dumps(entry, indent=2))

    elif args.command == "chat":
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query)
        response = supervisor.query_supervisory_chat(query)
        print(json.dumps({"query": query, "response": response}, indent=2))

    elif args.command == "verify-audit":
        from agents.base import AuditLogger
        valid = AuditLogger.verify_integrity()
        trail_len = len(AuditLogger.get_trail())
        result = {"audit_valid": valid, "trail_length": trail_len}
        print(json.dumps(result, indent=2))

    elif args.command == "serve":
        try:
            import uvicorn
            from agents.api import app
            uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("Error: uvicorn and fastapi required. Install with: pip install fastapi uvicorn", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
