"""
Tests for Phenytoin Winter-Tozer Correction Calculator.
"""
import os
import warnings
import pytest
from winter_tozer import (
    correct_phenytoin_normal,
    correct_phenytoin_renal,
    correct_phenytoin,
    interpret_phenytoin,
    calculate_steady_state_mm,
    estimate_vmax_km_from_two_levels,
    predict_dose_for_target_css,
    calculate_loading_dose,
    saturation_kinetics_warning,
    full_phenytoin_assessment,
    main,
    TOTAL_THERAPEUTIC_LOW,
    TOTAL_THERAPEUTIC_HIGH,
    DEFAULT_VMAX,
    DEFAULT_KM,
)


# ============================================================================
# Winter-Tozer Normal Tests
# ============================================================================

class TestWinterTozerNormal:
    def test_normal_albumin(self):
        # Corrected = 10 / ((0.25 * 4.0) + 0.1) = 10 / 1.1 = 9.09
        result = correct_phenytoin_normal(10.0, 4.0)
        assert abs(result["corrected_phenytoin_mg_l"] - 9.1) < 0.1

    def test_low_albumin(self):
        # Corrected = 8 / ((0.25 * 2.0) + 0.1) = 8 / 0.6 = 13.33
        result = correct_phenytoin_normal(8.0, 2.0)
        assert abs(result["corrected_phenytoin_mg_l"] - 13.3) < 0.1

    def test_very_low_albumin(self):
        result = correct_phenytoin_normal(6.0, 1.5)
        # Corrected = 6 / ((0.25 * 1.5) + 0.1) = 6 / 0.475 = 12.63
        assert abs(result["corrected_phenytoin_mg_l"] - 12.6) < 0.1

    def test_high_albumin(self):
        result = correct_phenytoin_normal(15.0, 5.0)
        # Corrected = 15 / ((0.25 * 5.0) + 0.1) = 15 / 1.35 = 11.11
        assert abs(result["corrected_phenytoin_mg_l"] - 11.1) < 0.1

    def test_zero_albumin_raises(self):
        with pytest.raises(ValueError):
            correct_phenytoin_normal(10.0, 0)

    def test_negative_phenytoin_raises(self):
        with pytest.raises(ValueError):
            correct_phenytoin_normal(-1.0, 4.0)

    def test_formula_string(self):
        result = correct_phenytoin_normal(10.0, 4.0)
        assert "0.25" in result["correction_formula"]
        assert result["renal_adjustment"] is False


# ============================================================================
# Winter-Tozer Renal Tests
# ============================================================================

class TestWinterTozerRenal:
    def test_renal_formula(self):
        # Corrected = 10 / ((0.1 * 4.0) + 0.1) = 10 / 0.5 = 20.0
        result = correct_phenytoin_renal(10.0, 4.0)
        assert abs(result["corrected_phenytoin_mg_l"] - 20.0) < 0.1

    def test_renal_gives_higher_correction(self):
        normal = correct_phenytoin_normal(10.0, 3.0)
        renal = correct_phenytoin_renal(10.0, 3.0)
        assert renal["corrected_phenytoin_mg_l"] > normal["corrected_phenytoin_mg_l"]

    def test_renal_flag(self):
        result = correct_phenytoin_renal(10.0, 4.0)
        assert result["renal_adjustment"] is True
        assert "0.1" in result["correction_formula"]


# ============================================================================
# Auto-Selection Tests
# ============================================================================

class TestCorrectPhenytoin:
    def test_normal_crcl(self):
        result = correct_phenytoin(10.0, 3.0, crcl_ml_min=80)
        assert result["renal_adjustment"] is False

    def test_low_crcl(self):
        result = correct_phenytoin(10.0, 3.0, crcl_ml_min=5)
        assert result["renal_adjustment"] is True

    def test_no_crcl(self):
        result = correct_phenytoin(10.0, 3.0)
        assert result["renal_adjustment"] is False

    def test_has_interpretation(self):
        result = correct_phenytoin(10.0, 4.0)
        assert "interpretation" in result
        assert "status" in result["interpretation"]


# ============================================================================
# Interpretation Tests
# ============================================================================

class TestInterpretation:
    def test_therapeutic(self):
        result = interpret_phenytoin(15.0)
        assert result["status"] == "THERAPEUTIC"

    def test_subtherapeutic(self):
        result = interpret_phenytoin(5.0)
        assert result["status"] == "SUBTHERAPEUTIC"

    def test_mildly_toxic(self):
        result = interpret_phenytoin(25.0)
        assert result["status"] == "MILDLY_TOXIC"

    def test_moderately_toxic(self):
        result = interpret_phenytoin(35.0)
        assert result["status"] == "MODERATELY_TOXIC"

    def test_severely_toxic(self):
        result = interpret_phenytoin(45.0)
        assert result["status"] == "SEVERELY_TOXIC"

    def test_boundary_low(self):
        result = interpret_phenytoin(10.0)
        assert result["status"] == "THERAPEUTIC"

    def test_boundary_high(self):
        result = interpret_phenytoin(20.0)
        assert result["status"] == "THERAPEUTIC"

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            interpret_phenytoin(-1)


# ============================================================================
# Michaelis-Menten Tests
# ============================================================================

class TestMichaelisMenten:
    def test_steady_state(self):
        result = calculate_steady_state_mm(300)
        assert result["predicted_css_mg_l"] > 0
        assert "interpretation" in result

    def test_higher_dose_higher_css(self):
        low = calculate_steady_state_mm(200)
        high = calculate_steady_state_mm(400)
        assert high["predicted_css_mg_l"] > low["predicted_css_mg_l"]

    def test_saturation_nonlinearity(self):
        # M-M kinetics: concentration approaches Vmax asymptotically
        # At very high doses, increases become smaller (saturation)
        css_low = calculate_steady_state_mm(100)["predicted_css_mg_l"]
        css_mid = calculate_steady_state_mm(200)["predicted_css_mg_l"]
        css_high = calculate_steady_state_mm(400)["predicted_css_mg_l"]
        # All should be positive and increasing
        assert css_mid > css_low
        assert css_high > css_mid
        # But the ratio of css increase to dose increase should decrease
        # (diminishing returns at higher doses = saturation)
        ratio_low = css_mid / 200  # css per mg at low dose
        ratio_high = css_high / 400  # css per mg at high dose
        assert ratio_high < ratio_low  # Saturation: less efficient at higher doses

    def test_custom_params(self):
        result = calculate_steady_state_mm(300, vmax_mg_per_day=600, km_mg_l=5.0)
        assert result["predicted_css_mg_l"] > 0

    def test_invalid_dose(self):
        with pytest.raises(ValueError):
            calculate_steady_state_mm(0)


# ============================================================================
# Vmax/Km Estimation Tests
# ============================================================================

class TestVmaxKmEstimation:
    def test_estimation(self):
        # Use data consistent with Css = (Vmax*D)/(Km+D)
        # With Vmax=500, Km=100: D=200->Css=333.3, D=300->Css=375
        result = estimate_vmax_km_from_two_levels(200, 333.33, 300, 375.0)
        assert result["estimated_vmax_mg_per_day"] > 0
        assert result["estimated_km_mg_l"] > 0
        assert abs(result["estimated_vmax_mg_per_day"] - 500) < 1
        assert abs(result["estimated_km_mg_l"] - 100) < 1

    def test_same_concentrations_raises(self):
        with pytest.raises(ValueError):
            estimate_vmax_km_from_two_levels(200, 10.0, 300, 10.0)

    def test_invalid_doses(self):
        with pytest.raises(ValueError):
            estimate_vmax_km_from_two_levels(0, 8.5, 300, 18.2)


# ============================================================================
# Target Dose Prediction Tests
# ============================================================================

class TestTargetDosePrediction:
    def test_prediction(self):
        result = predict_dose_for_target_css(15.0)
        assert result["predicted_daily_dose_mg"] > 0

    def test_higher_target_higher_dose(self):
        low = predict_dose_for_target_css(10.0)
        high = predict_dose_for_target_css(18.0)
        assert high["predicted_daily_dose_mg"] > low["predicted_daily_dose_mg"]


# ============================================================================
# Loading Dose Tests
# ============================================================================

class TestLoadingDose:
    def test_standard(self):
        result = calculate_loading_dose(15.0, weight_kg=70)
        assert result["loading_dose_mg"] > 0
        assert result["loading_dose_mg_per_kg"] > 0

    def test_higher_target(self):
        low = calculate_loading_dose(10.0, weight_kg=70)
        high = calculate_loading_dose(20.0, weight_kg=70)
        assert high["loading_dose_mg"] > low["loading_dose_mg"]

    def test_oral_dosing_info(self):
        result = calculate_loading_dose(15.0, weight_kg=70)
        assert result["oral_dosing"]["max_single_dose_mg"] == 400

    def test_invalid_target(self):
        with pytest.raises(ValueError):
            calculate_loading_dose(0, weight_kg=70)


# ============================================================================
# Saturation Warning Tests
# ============================================================================

class TestSaturationWarning:
    def test_low_dose_no_warning(self):
        result = saturation_kinetics_warning(200, 50)
        assert result["risk_level"] in ["LOW", "MODERATE"]

    def test_high_dose_warning(self):
        result = saturation_kinetics_warning(400, 100)
        assert result["risk_level"] == "HIGH"
        assert len(result["warnings"]) > 0

    def test_large_increase_warning(self):
        result = saturation_kinetics_warning(300, 200)
        assert len(result["warnings"]) > 0


# ============================================================================
# Full Assessment Tests
# ============================================================================

class TestFullAssessment:
    def test_basic_assessment(self):
        result = full_phenytoin_assessment(12.0, 3.5)
        assert "correction" in result
        assert "interpretation" in result
        assert "corrected_phenytoin_mg_l" in result

    def test_assessment_with_dose(self):
        result = full_phenytoin_assessment(12.0, 3.5, daily_dose_mg=300)
        assert result["steady_state_prediction"] is not None

    def test_assessment_with_renal(self):
        result = full_phenytoin_assessment(12.0, 3.5, crcl_ml_min=5)
        assert result["correction"]["renal_adjustment"] is True

    def test_disclaimer_present(self):
        result = full_phenytoin_assessment(12.0, 3.5)
        assert "disclaimer" in result


# ============================================================================
# CLI Tests
# ============================================================================

class TestCLI:
    def test_correct_command(self):
        ret = main(["correct", "--phenytoin", "8.0", "--albumin", "2.5"])
        assert ret == 0

    def test_correct_with_crcl(self):
        ret = main(["correct", "--phenytoin", "8.0", "--albumin", "2.5", "--crcl", "5"])
        assert ret == 0

    def test_steady_state_command(self):
        ret = main(["steady-state", "--dose", "300"])
        assert ret == 0

    def test_estimate_params_command(self):
        ret = main(["estimate-params", "--dose1", "200", "--css1", "333.33",
                     "--dose2", "300", "--css2", "375.0"])
        assert ret == 0

    def test_loading_dose_command(self):
        ret = main(["loading-dose", "--target", "15", "--weight", "70"])
        assert ret == 0

    def test_assess_command(self):
        ret = main(["assess", "--phenytoin", "12.0", "--albumin", "3.5"])
        assert ret == 0

    def test_audit_command(self):
        ret = main(["audit", "--task-id", "TEST-AUDIT-001"])
        assert ret == 0

    def test_audit_command_with_actor(self):
        ret = main(["audit", "--task-id", "TEST-AUDIT-002", "--actor", "test-user", "--event-type", "TEST_EVENT"])
        assert ret == 0

    def test_chat_command(self):
        ret = main(["chat", "Explain", "phenytoin", "kinetics"])
        assert ret == 0

    def test_verify_audit_command(self):
        ret = main(["verify-audit"])
        assert ret == 0


# ============================================================================
# Security Tests
# ============================================================================

class TestSecurity:
    def test_audit_trail_no_hardcoded_key(self):
        """Verify that AuditTrail generates a random key when no secret is provided."""
        from agents.base import AuditTrail
        # Ensure no env var is set for this test
        original = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                trail = AuditTrail()
            # Key should be 32 bytes (random), not a hardcoded string
            assert len(trail.secret_key) == 32
        finally:
            if original is not None:
                os.environ["AUDIT_SECRET_KEY"] = original

    def test_audit_trail_uses_env_key_when_set(self):
        """Verify that AuditTrail uses the AUDIT_SECRET_KEY env var when set."""
        from agents.base import AuditTrail
        original = os.environ.get("AUDIT_SECRET_KEY")
        os.environ["AUDIT_SECRET_KEY"] = "test-secret-key-for-unit-test"
        try:
            trail = AuditTrail()
            assert trail.secret_key == b"test-secret-key-for-unit-test"
        finally:
            if original is not None:
                os.environ["AUDIT_SECRET_KEY"] = original
            else:
                del os.environ["AUDIT_SECRET_KEY"]

    def test_phi_guard_blocks_mrn(self):
        from agents.base import PHIGuard, SecurityException
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_phi_guard_blocks_ssn(self):
        from agents.base import PHIGuard, SecurityException
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phi_guard_blocks_email(self):
        from agents.base import PHIGuard, SecurityException
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Contact patient@example.com for results")

    def test_phi_guard_allows_clean_text(self):
        from agents.base import PHIGuard
        # Should not raise
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")

    def test_phi_redaction(self):
        from agents.base import PHIGuard
        redacted = PHIGuard.redact_phi("Patient MRN-12345678 and SSN 123-45-6789")
        assert "MRN" not in redacted or "REDACTED" in redacted
        assert "123-45-6789" not in redacted
