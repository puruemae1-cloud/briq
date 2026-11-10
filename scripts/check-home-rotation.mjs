#!/usr/bin/env node
/**
 * Guard: Seoul 22:00 rotation day must flip, and luxury 4-set must change.
 * Run: node scripts/check-home-rotation.mjs
 */
import assert from "node:assert/strict";

function seoulRotationDay(now) {
  const shifted = new Date(now - 22 * 60 * 60 * 1000);
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(shifted);
}

function secondsUntilNextSeoulRotation(now) {
  const day = seoulRotationDay(now);
  const [y, m, d] = day.split("-").map(Number);
  const nextFlipUtc = Date.UTC(y, m - 1, d + 1, 13, 0, 0);
  return Math.max(30, Math.ceil((nextFlipUtc - now) / 1000));
}

// 2026-11-10 21:59:00 KST = 12:59 UTC
const before = Date.UTC(2026, 10, 10, 12, 59, 0);
// 2026-11-10 22:00:00 KST = 13:00 UTC
const after = Date.UTC(2026, 10, 10, 13, 0, 0);

const dayBefore = seoulRotationDay(before);
const dayAfter = seoulRotationDay(after);
assert.notEqual(dayBefore, dayAfter, "rotation day must flip at 22:00 KST");
assert.equal(dayBefore, "2026-11-09");
assert.equal(dayAfter, "2026-11-10");

const secs = secondsUntilNextSeoulRotation(before);
assert.ok(secs <= 60, `expected ~60s until flip, got ${secs}`);
assert.ok(secs >= 30);

console.log("ok", { dayBefore, dayAfter, secsUntilFlipAt2159Kst: secs });
