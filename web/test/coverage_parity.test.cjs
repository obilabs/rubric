/*
 * coverage_parity.test.cjs — proves the JS coverage engine that drives the
 * playground's "what to drill" diagnosis computes the SAME blueprint coverage
 * as the reference Python `Bundle.coverage` / `rubric blueprint`.
 *
 * For every bundled example bank it parses all questions, runs
 * Rubric.coverage(manifest, data), and compares against the golden produced by
 * `python tests/conformance/build.py`. A drift in the weighting math — the
 * heart of differentiator #2 — turns this red.
 *
 *     node web/test/coverage_parity.test.cjs
 */
"use strict";

const fs = require("fs");
const path = require("path");

const Rubric = require("../rubric.js");

const REPO = path.resolve(__dirname, "..", "..");
const EXAMPLES = path.join(REPO, "examples");
const COV_DIR = path.join(REPO, "tests", "conformance", "expected_coverage");

function canonical(value) {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    return (
      "{" +
      keys.map((k) => JSON.stringify(k) + ":" + canonical(value[k])).join(",") +
      "}"
    );
  }
  return JSON.stringify(value);
}

function findManifests(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...findManifests(full));
    else if (entry.name === "manifest.json") out.push(full);
  }
  return out.sort();
}

function bundleIdFor(manifest, root) {
  const cert = manifest.certification || {};
  return (
    cert.slug ||
    manifest.slug ||
    path.relative(EXAMPLES, root).replace(/[\\/]/g, "-")
  );
}

function main() {
  if (!fs.existsSync(COV_DIR)) {
    console.error("No coverage goldens. Run: python tests/conformance/build.py");
    process.exit(2);
  }

  const manifests = findManifests(EXAMPLES);
  let passed = 0;
  const failures = [];

  for (const manifestPath of manifests) {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
    const root = path.dirname(manifestPath);
    const id = bundleIdFor(manifest, root);
    const goldenPath = path.join(COV_DIR, id + ".json");
    if (!fs.existsSync(goldenPath)) {
      failures.push({ id, why: "no golden at " + goldenPath });
      continue;
    }

    const rel = Array.isArray(manifest.question_files) ? manifest.question_files : [];
    // Match Python Bundle.coverage: count EVERY successfully-parsed question's
    // domains (not only choice questions).
    const data = [];
    for (const qrel of rel) {
      const res = Rubric.parse(fs.readFileSync(path.join(root, qrel), "utf-8"));
      if (res.success && res.data) data.push(res.data);
    }

    const actual = Rubric.coverage(manifest, data);
    const expected = JSON.parse(fs.readFileSync(goldenPath, "utf-8"));

    if (canonical(actual) === canonical(expected)) {
      passed += 1;
    } else {
      failures.push({
        id,
        why: "coverage differs from golden",
        expected: JSON.stringify(expected, null, 2),
        actual: JSON.stringify(actual, null, 2),
      });
    }
  }

  console.log(
    `Coverage parity: ${passed}/${manifests.length} banks match the Python reference.`
  );

  if (failures.length) {
    console.error("\n" + failures.length + " FAILED:\n");
    for (const f of failures) {
      console.error("  ✗ " + f.id + " — " + f.why);
      if (f.expected) {
        console.error("    expected:\n" + f.expected);
        console.error("    actual:\n" + f.actual);
      }
    }
    process.exit(1);
  }
  console.log("All banks' coverage matches. The diagnosis engine is in lockstep.");
}

main();
