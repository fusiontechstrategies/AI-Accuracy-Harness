# Qualification Report

Decision: **QUALIFIED FOR NARROW HYBRID PROPOSAL-ONLY USE**

## Local lane

The package references the separately sealed `Accuracy-Harness-v4.0-Structural-Managed` qualification for `devstral-small-2:24b-instruct-2512-q4_K_M`, digest `24277f07f62db8f9cb68e9dfc679ea1818a7fbac47a50eff0a701d3f645b63c8`. That qualification passed 12 of 12 structural extraction executions over three sealed runs with no repair calls, retries, gate failures, or source-restoration failures. The authorization remains limited to its deterministic Python test-function extraction adapter.

## Cerebras bounded lane

- Exact model: `openai/gpt-oss-120b`
- Exact provider: `Cerebras`
- Provider fallback: denied
- Provider data collection: denied
- Worker authority: proposal only
- Case plan: 13 real project and safety cases
- Repeats: 3
- Calls: 39
- Passed: 39
- Failed: 0
- Repairs: 0
- Reported series cost: $0.1255677
- Median latency: 1.867 seconds
- 95th percentile latency: 6.158 seconds
- Maximum latency: 8.239 seconds
- Case-plan SHA-256: `7AD1428B47BBB9F8E003EE1C35D4D04242562718BAF1F7AF58CC61B523BF9F00`
- Summary SHA-256: `F9CA78C37F7A59518FEF7C9013B654DF5AFA5C111BA91FCD70308440A3858140`

The packaged live self-test then passed with the exact model and provider in 0.689 seconds. Independent evidence replay verified all eight sealed files and reproduced the proposal from the raw stored response. An isolated one-field proposal alteration was rejected with an evidence hash mismatch.

## Negative security qualification

The same model and provider are **not qualified for open-ended security review**.

Two high-reasoning three-call whole-file audits produced no schema-valid responses because the observed provider output stopped at 8,192 completion tokens while still emitting reasoning. A medium-reasoning three-call run produced schema-valid reports, but comparison against independently known defects showed critical misses and likely false positives. Targeted invariant probes recovered one authenticated-state rollback defect, identified part of a nested capability-lifetime class with imprecise evidence, and still produced an unsupported claim.

This is a useful negative result. Fast, fluent, schema-valid output is not proof of security accuracy. Security review remains lead-only, with model output treated as a hypothesis that must be reproduced by a deterministic exploit or regression test.

## Harness integrity

- Eighteen current unit and adversarial tests pass.
- Exact provider and model identity are enforced.
- No price or token-cost budget is imposed by the worker.
- The endpoint's advertised maximum completion allowance is requested.
- Strict response schema, duplicate-key rejection, and non-finite rejection are enforced locally.
- Incomplete responses, provider drift, model drift, fallback, and missing candidates fail closed.
- Retryable throttling is checkpointed without overwriting earlier attempts.
- The OpenRouter key is not persisted and completed evidence is scanned for accidental disclosure.
- Complete evidence sealing and independent replay are implemented.
- A one-field tampering test fails closed.
- Hybrid routing prevents remote use for restricted data and prevents worker admission for high-risk, open-security, editing, external-action, or oracle-free tasks.

## Meaning of this decision

The harness may reduce lead-model token use and elapsed proposal time for exact qualified lanes. It does not reduce the required regression, security, VM, scanner, installer, signing, or independent-review gates. No worker output is approval, and no qualification transfers automatically to a new adapter or project.
