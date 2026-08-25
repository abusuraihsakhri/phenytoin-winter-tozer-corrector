# Phenytoin Winter-Tozer Correction Calculator

Real clinical calculator for correcting measured phenytoin levels in hypoalbuminemia and renal impairment, with Michaelis-Menten kinetics for dose adjustment.

## Clinical Background

Phenytoin is highly protein-bound (~90% to albumin). In hypoalbuminemia, the measured total phenytoin level underestimates the free (active) fraction. The **Winter-Tozer equation** corrects for this:

- **Normal renal function:** `Corrected = Measured / ((0.25 × albumin) + 0.1)`
- **Renal impairment (CrCl <10):** `Corrected = Measured / ((0.1 × albumin) + 0.1)`

Phenytoin follows **Michaelis-Menten (zero-order) kinetics** at therapeutic doses, meaning small dose increases can cause disproportionately large concentration increases.

## Key Formulas

| Parameter | Formula |
|-----------|---------|
| Winter-Tozer (normal) | `Corrected = Measured / ((0.25 × albumin) + 0.1)` |
| Winter-Tozer (renal) | `Corrected = Measured / ((0.1 × albumin) + 0.1)` |
| Michaelis-Menten | `Css = (Vmax × Dose) / (Km + Dose)` |
| Vmax/Km estimation | Two-level method using simultaneous equations |
| Loading dose | `LD = (Vd × Ctarget) / F` |

## Therapeutic Ranges

| Measurement | Range |
|-------------|-------|
| Total phenytoin | 10-20 mg/L |
| Free phenytoin | 1-2 mg/L |
| Corrected phenytoin | 10-20 mg/L (use for dosing decisions) |

## Installation

```bash
# No dependencies required - Python 3.8+ stdlib only
cd phenytoin-winter-tozer-corrector
```

## Usage

### Correct Phenytoin Level
```bash
python cli.py correct --phenytoin 8.0 --albumin 2.5
python cli.py correct --phenytoin 8.0 --albumin 2.5 --crcl 8
```

### Predict Steady-State from Dose
```bash
python cli.py steady-state --dose 300
python cli.py steady-state --dose 400 --vmax 500 --km 5.0
```

### Estimate Individual Vmax/Km
```bash
python cli.py estimate-params --dose1 200 --css1 8.5 --dose2 300 --css2 18.2
```

### Calculate Loading Dose
```bash
python cli.py loading-dose --target 15 --weight 70
```

### Full Assessment
```bash
python cli.py assess --phenytoin 8.0 --albumin 2.5
python cli.py assess --phenytoin 12.0 --albumin 3.0 --crcl 8 --dose 300 --weight 70
```

## Output Format

All commands output JSON. Example:
```json
{
  "measured_phenytoin_mg_l": 8.0,
  "albumin_g_dl": 2.5,
  "corrected_phenytoin_mg_l": 11.4,
  "correction_formula": "Measured / ((0.25 * albumin) + 0.1)",
  "renal_adjustment": false,
  "interpretation": {
    "status": "THERAPEUTIC",
    "recommendation": "Within therapeutic range. Continue current regimen."
  }
}
```

## Tests

```bash
python -m pytest test_winter_tozer.py -v
```

## Disclaimer

**FOR EDUCATIONAL AND RESEARCH USE ONLY.** This calculator is not a substitute for clinical pharmacist review. Phenytoin dosing requires consideration of drug interactions, hepatic function, and individual patient factors.

## References

- Winter ME, Tozer TN. Phenytoin. In: Evans WE, et al., eds. *Applied Pharmacokinetics*. 3rd ed. Vancouver, WA: Applied Therapeutics; 1986.
- Anderson GD. A mechanistic approach to antiepileptic drug interactions. *Ann Pharmacother*. 1998;32(5):554-563.
- Tozer TN, Winter ME. Phenytoin. In: Burton ME, et al., eds. *Applied Clinical Pharmacokinetics*. 2nd ed. New York: McGraw-Hill; 2005.

## License

MIT License. See [LICENSE](LICENSE) for details.
