"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { calculateCorrection } = require("./app.js");

test("standard calculation and albumin units", () => {
  const result = calculateCorrection(8, 2);
  assert.equal(result.renal, false);
  assert.ok(Math.abs(result.corrected - 13.3333333333) < 1e-8);
  assert.equal(result.coefficient, 0.25);
});
test("legacy renal coefficient below CrCl 10", () => {
  assert.ok(Math.abs(calculateCorrection(8, 2, 5).corrected - 8 / 0.3) < 1e-8);
  assert.equal(calculateCorrection(8, 2, 10).renal, false);
  assert.equal(calculateCorrection(8, 2, null).renal, false);
});
test("zero total is valid; invalid inputs are rejected", () => {
  assert.equal(calculateCorrection(0, 4).corrected, 0);
  for (const total of [NaN, Infinity, -1]) assert.throws(() => calculateCorrection(total, 4), RangeError);
  for (const albumin of [NaN, Infinity, 0, -1]) assert.throws(() => calculateCorrection(8, albumin), RangeError);
  for (const crcl of [NaN, Infinity, -1]) assert.throws(() => calculateCorrection(8, 2, crcl), RangeError);
});
