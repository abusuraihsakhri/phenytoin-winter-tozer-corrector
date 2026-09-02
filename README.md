# Phenytoin Winter Tozer Corrector

> **Domain:** Clinical Pharmacology & Precision Pharmacotherapy  
> **Reference Guidelines & Standards:** `CPIC Guidelines & FDA Table of Pharmacogenomic Biomarkers`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

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

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`correct_phenytoin_normal()`**: Correct phenytoin level for hypoalbuminemia (normal renal function).

Winter-Tozer equation:
Corrected = Measured / ((0.25 * albumin) + 0.1)

Args:
    measured_phenytoin_mg_l: Measured total phenytoin in mg/L
    albumin_g_dl: Serum albumin in g/dL
    
Returns:
    Dictionary with corrected phenytoin and interpretation
- **`correct_phenytoin_renal()`**: Correct phenytoin level for hypoalbuminemia with renal impairment.

Modified Winter-Tozer for ESRD/CrCl <10:
Corrected = Measured / ((0.1 * albumin) + 0.1)

Args:
    measured_phenytoin_mg_l: Measured total phenytoin in mg/L
    albumin_g_dl: Serum albumin in g/dL
    
Returns:
    Dictionary with corrected phenytoin and interpretation
- **`correct_phenytoin()`**: Correct phenytoin level using appropriate Winter-Tozer equation.

Automatically selects renal-adjusted formula if CrCl < 10 mL/min.

Args:
    measured_phenytoin_mg_l: Measured total phenytoin in mg/L
    albumin_g_dl: Serum albumin in g/dL
    crcl_ml_min: Creatinine clearance in mL/min (optional)
    
Returns:
    Dictionary with corrected phenytoin and interpretation
- **`interpret_phenytoin()`**: Interpret corrected phenytoin concentration.

Args:
    corrected_mg_l: Corrected total phenytoin in mg/L
    
Returns:
    Dictionary with interpretation
- **`calculate_steady_state_mm()`**: Calculate steady-state phenytoin concentration using Michaelis-Menten kinetics.

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

---

## 📐 Mathematical Formulation & Logic

```text
  Key formulas:
  "correction_formula": "Measured / ((0.25 * albumin) + 0.1)",
  "correction_formula": "Measured / ((0.1 * albumin) + 0.1)",
  Automatically selects renal-adjusted formula if CrCl < 10 mL/min.
  risk = "Seizure breakthrough risk"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t phenytoin-winter-tozer-corrector .
docker run -p 8000:8000 phenytoin-winter-tozer-corrector
```
