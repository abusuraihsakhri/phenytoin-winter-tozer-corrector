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
- Normal albumin: `Corrected = Measured / ((0.25 * albumin) + 0.1)`
- Renal impairment (CrCl <10): `Corrected = Measured / ((0.1 * albumin) + 0.1)`
- Michaelis-Menten: `Css = (Vmax * Dose/tau) / (Km + Dose/tau)`
- Steady state estimation from two levels
- Loading dose calculation

Therapeutic range: 10-20 mg/L (total), 1-2 mg/L (free)

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`correct_phenytoin_normal()`**: Correct phenytoin level for hypoalbuminemia (normal renal function).
- **`correct_phenytoin_renal()`**: Correct phenytoin level for hypoalbuminemia with renal impairment.
- **`correct_phenytoin()`**: Auto-selects renal-adjusted formula if CrCl < 10 mL/min.
- **`interpret_phenytoin()`**: Interpret corrected phenytoin concentration.
- **`calculate_steady_state_mm()`**: Calculate steady-state phenytoin concentration using Michaelis-Menten kinetics.
- **`estimate_vmax_km_from_two_levels()`**: Estimate individual Vmax and Km from two steady-state dose/concentration pairs.
- **`predict_dose_for_target_css()`**: Predict daily dose needed to achieve target steady-state concentration.
- **`calculate_loading_dose()`**: Calculate phenytoin loading dose.
- **`saturation_kinetics_warning()`**: Warn about phenytoin saturation kinetics.
- **`full_phenytoin_assessment()`**: Complete phenytoin assessment with correction and dosing guidance.

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/phenytoin-winter-tozer-corrector.git
cd phenytoin-winter-tozer-corrector

# Install dependencies (for API server)
pip install fastapi uvicorn pydantic pytest
```

---

## 💻 CLI Quickstart & Usage

### 1. Correct Phenytoin Level
```bash
python cli.py correct --phenytoin 8.0 --albumin 2.5
python cli.py correct --phenytoin 8.0 --albumin 2.5 --crcl 5
```

### 2. Predict Steady-State Concentration
```bash
python cli.py steady-state --dose 300
python cli.py steady-state --dose 300 --vmax 600 --km 5.0
```

### 3. Estimate Vmax/Km from Two Levels
```bash
python cli.py estimate-params --dose1 200 --css1 333.33 --dose2 300 --css2 375.0
```

### 4. Calculate Loading Dose
```bash
python cli.py loading-dose --target 15 --weight 70
```

### 5. Full Assessment
```bash
python cli.py assess --phenytoin 12.0 --albumin 3.5 --dose 300
```

### 6. Audit Operations
```bash
python cli.py audit --task-id "TASK-001"
python cli.py chat "Explain phenytoin kinetics"
python cli.py verify-audit
```

### 7. Start REST API Server
```bash
python cli.py serve --host 0.0.0.0 --port 8000
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable for persistent tamper-evident audit across restarts:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key-here"

# Windows
set AUDIT_SECRET_KEY=your-secure-random-key-here
```

Without this variable, an ephemeral random key is generated at startup (audit entries will not persist across restarts).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t phenytoin-winter-tozer-corrector .
docker run -p 8000:8000 phenytoin-winter-tozer-corrector
```

---

## 📐 Mathematical Formulation

```
Winter-Tozer (normal):  Corrected = Measured / ((0.25 * albumin) + 0.1)
Winter-Tozer (renal):   Corrected = Measured / ((0.1 * albumin) + 0.1)
Michaelis-Menten:       Css = (Vmax * Dose) / (Km * F * 1000 + Dose)
Loading Dose:           LD = (Vd * target * weight) / F
```

---

## ⚠️ Disclaimer

**FOR EDUCATIONAL/RESEARCH USE ONLY.** Not a substitute for clinical pharmacist review.
