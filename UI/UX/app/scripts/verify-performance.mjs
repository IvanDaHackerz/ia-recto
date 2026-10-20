import assert from "node:assert/strict";
import fs from "node:fs";
import { reportFor, routingFor } from "../src/data/performance.ts";

const bundle = JSON.parse(fs.readFileSync(new URL("../../../../tmp/website-integration-performance.json", import.meta.url), "utf8"));
let comparisons = 0;
const close = (a, b) => { assert.ok(Math.abs(a - b) < 1e-9, a + " != " + b); comparisons++; };
for (const data of [bundle, bundle.historical_report].filter(Boolean)) {
for (const stratum of ["all", "clear", "noisy"]) {
  const rows = data.cases.filter(r => stratum === "all" || r.variation === stratum);
  for (const path of data.available_paths) {
    const expected = data.metrics.strata[stratum][path];
    for (const head of ["domain", "scope"]) {
      const actual = reportFor(rows, path, head);
      const saved = expected[head === "domain" ? "primary" : head];
      assert.equal(actual.correct, saved.accuracy.numerator);
      assert.equal(actual.total, saved.accuracy.denominator);
      close(actual.accuracy, saved.accuracy.value);
      close(actual.macroF1, saved.macro_f1);
      close(actual.ece, saved.confidence_calibration.ece);
      assert.deepEqual(actual.matrix, saved.confusion.counts);
      for (const c of actual.classes) {
        assert.equal(c.support, saved.per_class[c.label].support);
        close(c.precision, saved.per_class[c.label].precision);
        close(c.recall, saved.per_class[c.label].recall);
        close(c.f1, saved.per_class[c.label].f1);
      }
    }
    const route = routingFor(rows, path);
    assert.equal(route.correct, expected.route_match.numerator);
    assert.equal(route.total, expected.route_match.denominator);
    assert.equal(route.hit, expected.known_relevant_hit_at_5.numerator);
    assert.equal(route.judged, expected.known_relevant_hit_at_5.denominator);
    close(route.median, expected.latency_ms.median);
    close(route.p95, expected.latency_ms.p95);
  }
}
for (const language of ["en", "en_tl"]) {
  const rows = data.cases.filter(r => r.language === language);
  const report = reportFor(rows, data.available_paths[0], "domain");
  assert.equal(report.total, rows.filter(r => r.labeled).length);
  assert.equal(report.matrix.flat().reduce((a,b) => a+b, 0), report.total);
}
}
assert.equal(reportFor([], "normalized", "domain").accuracy, null);
assert.equal(reportFor([], "normalized", "domain").ece, null);
assert.equal(routingFor([], "normalized").median, null);
const withheld = bundle.historical_report.cases.filter(r => r.labeled && r.paths.normalized.domain === "__abstain__");
assert.equal(withheld.length, 2);
assert.equal(reportFor(withheld, "normalized", "domain").correct, 0);
assert.equal(reportFor(withheld, "normalized", "domain").total, 2);
assert.equal(reportFor(withheld, "normalized", "domain").ece, null);
assert.equal(bundle.available_paths.length, 1);
assert.ok(bundle.cases.every(r => !("normalized" in r.paths)));
console.log("Saved-metric reconciliation passed: " + comparisons + " numeric comparisons, exact confusion matrices, language subsets, empty data and withheld-label denominators.");

