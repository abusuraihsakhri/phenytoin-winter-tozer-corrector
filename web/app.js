"use strict";

/**
 * Correct total phenytoin (mg/L) for albumin (g/dL).
 * Mirrors the legacy Python calculator: revised non-renal factor 0.25,
 * historical CrCl < 10 mL/min factor 0.10. This is not a free drug assay.
 */
function calculateCorrection(total, albumin, crcl = null) {
  if (!Number.isFinite(total) || total < 0) {
    throw new RangeError("Measured phenytoin must be finite and non-negative.");
  }
  if (!Number.isFinite(albumin) || albumin <= 0) {
    throw new RangeError("Albumin must be finite and greater than zero.");
  }
  if (crcl !== null && (!Number.isFinite(crcl) || crcl < 0)) {
    throw new RangeError("Creatinine clearance must be finite and non-negative.");
  }
  const renal = crcl !== null && crcl < 10;
  const coefficient = renal ? 0.10 : 0.25;
  const denominator = coefficient * albumin + 0.10;
  const corrected = total / denominator;
  return { corrected, denominator, coefficient, renal };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { calculateCorrection };
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("correction-form");
    const output = document.getElementById("result");
    if (!form || !output) return;
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      output.classList.remove("error");
      try {
        const totalText = document.getElementById("total").value.trim();
        const albuminText = document.getElementById("albumin").value.trim();
        const crclText = document.getElementById("crcl").value.trim();
        if (!totalText || !albuminText) {
          throw new RangeError("Enter both measured phenytoin and albumin.");
        }
        const total = Number(totalText);
        const albumin = Number(albuminText);
        const crcl = crclText === "" ? null : Number(crclText);
        const result = calculateCorrection(total, albumin, crcl);
        const status = result.corrected < 10 ? "Below conventional corrected-total range" :
          result.corrected <= 20 ? "Within conventional corrected-total range" :
          "Above conventional corrected-total range";
        output.textContent =
          "Corrected total estimate: " + result.corrected.toFixed(1) + " mg/L\n" +
          status + "\n" +
          "Formula: measured / ((" + result.coefficient.toFixed(2) +
          " × albumin) + 0.10)\n" +
          (result.renal ? "Historical severe-renal coefficient selected; accuracy is uncertain.\n" :
            "Non-renal revised coefficient selected.\n") +
          "This is an estimate, not measured free phenytoin. Clinical interpretation is required.";
      } catch (error) {
        output.classList.add("error");
        output.textContent = error instanceof Error ? error.message : "Unable to calculate.";
      }
    });
  });
}
