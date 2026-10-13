# Phenytoin Winter–Tozer Corrector

A browser and Python tool for estimating **corrected total phenytoin concentrations** from measured total levels and serum albumin. It also contains a research-only Michaelis–Menten model, a REST API, and an optional demonstrative audit subsystem.

**Educational/research use only.** The output is not a directly measured free phenytoin concentration and is not an automatic dosing recommendation.

## Browser calculator

Open **web/index.html** in a current browser, or use the Pages deployment when enabled. Enter measured **total phenytoin** in mg/L (equal numerically to µg/mL), **albumin** in g/dL (not g/L), and optionally creatinine clearance in mL/min. The result shows the corrected-total estimate, selected coefficient and conventional-range category.

Calculations run locally in standard JavaScript, without external scripts, trackers, network requests, cookies or persistent storage. No server or Pyodide is needed.

## Correction equations and caveats

The project preserves the existing coefficient choices:

| Legacy selection | Corrected total (mg/L) |
| --- | --- |
| No CrCl or CrCl >= 10 mL/min | Measured total / (0.25 × albumin + 0.1) |
| CrCl < 10 mL/min | Measured total / (0.10 × albumin + 0.1) |

Albumin is in g/dL. The first coefficient is a revised non-renal variant; the second is the historical severe-renal variant. The original equation also used a 0.20 coefficient. The **CrCl 10 mL/min threshold is inherited software logic, not an independently validated clinical rule**. Prediction errors are common in critical illness and altered binding states.

The conventional total concentration interval is 10–20 mg/L. Interpret concentrations in the context of symptoms, collection time, interacting drugs, nutritional status and renal function. **Directly measured free phenytoin** is preferred in hypoalbuminemia, major kidney dysfunction or critical illness; do not make dose changes solely from an estimate.

Evidence: [review of Winter–Tozer and variants](https://pubmed.ncbi.nlm.nih.gov/26825643/), [kidney function and prediction accuracy](https://pubmed.ncbi.nlm.nih.gov/31067355/), [comparison against directly measured free phenytoin](https://pmc.ncbi.nlm.nih.gov/articles/PMC9237157/).

## Python CLI

Python 3.10–3.12:

    python -m pip install -r requirements-dev.txt
    python cli.py correct --phenytoin 8 --albumin 2.5
    python cli.py correct --phenytoin 8 --albumin 2.5 --crcl 5
    python cli.py assess --phenytoin 12 --albumin 3.5
    python -m pytest -q

Other preserved commands: **steady-state**, **estimate-params**, **loading-dose**, **audit**, **chat**, **verify-audit** and **serve**. Run **python cli.py --help** for usage.

The research-only model uses saturable elimination:

    F × dose_rate = Vmax × Css / (Km + Css)
    Css = Km × F × dose_rate / (Vmax - F × dose_rate)

Vmax and dose rate are in mg/day; Km and Css are in mg/L. No finite modeled steady state exists if F × dose rate is at least Vmax. Two-point fitting requires steady-state measurements and constant bioavailability. Neither the population model nor arithmetic loading-dose calculations constitute prescribing advice.

## FastAPI and Docker

Start the optional API:

    python cli.py serve --host 127.0.0.1 --port 8000

The browser app is available at **http://127.0.0.1:8000/**, and generated API documentation at **http://127.0.0.1:8000/docs**. The stateless **POST /api/correct** accepts JSON with the measured_phenytoin_mg_l and albumin_g_dl fields and optional crcl_ml_min.

**/api/audit**, **/api/chat** and **/api/audit/logs** are demo-only and require an **X-API-Key** header matching the **AUDIT_API_KEY** environment variable. They return 503 if no server key has been configured. The chat provider is a mock, not a clinical model. The HMAC audit trail is process-local, not a durable record. Regex screening is not guaranteed patient-data de-identification; do not submit PHI. **/metrics** returns JSON, not Prometheus text.

For Docker Compose, set strong, private **AUDIT_SECRET_KEY** and **AUDIT_API_KEY** environment variables, then run:

    docker compose up --build

Never commit secrets. Rotate any key previously committed in the repository history.

## Testing, browser support and deployment

- Python: **python -m pytest -q** (CI matrix: Python 3.10–3.12).
- Browser JavaScript: **node --check web/app.js** and **node --test web/app.test.cjs**.
- Pages workflow publishes the static **web/** directory on pushes to **master**. Pages must be enabled with GitHub Actions as its source. The live URL will be documented once verified.
- Python calculations beyond basic correction, the FastAPI server, and audit functionality do **not** execute on Pages.
- Intended for modern Chrome, Firefox, Safari and Edge; a real-browser end-to-end test is needed before claiming verified compatibility.

## License

MIT. See [LICENSE](LICENSE).
