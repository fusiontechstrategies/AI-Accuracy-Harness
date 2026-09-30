# Results and interpretation

The included evidence summaries answer one narrow question: did the exact worker configuration
reliably produce contract-valid proposals for the preregistered task class while the harness
preserved its authority and integrity boundaries?

## Bounded structural qualification

| Measure | Result |
|---|---:|
| Model | `openai/gpt-oss-120b` |
| Required provider | Cerebras |
| Cases | 13 |
| Repeats per case | 3 |
| Calls | 39 |
| Passed | 39 |
| Failed | 0 |
| Repair calls | 0 |
| Reported total cost | $0.1255677 |
| Median latency | 1.867 seconds |
| 95th percentile latency | 6.158 seconds |
| Maximum latency | 8.239 seconds |

The qualified decision is limited to bounded structural selection among preregistered options.
Every accepted result still requires a deterministic project oracle and independent review.

## Packaged live self-test

The packaged self-test completed with the exact model and provider in 0.689 seconds at a reported
cost of $0.0007317. It produced one workflow-valid proposal eligible for independent review.
`promotion_authorized` and `semantic_approval` remained false.

## Integrity negative test

The tamper test changed one proposal field in an isolated evidence copy without updating the
receipt or seal. Independent verification rejected the copy with an evidence hash mismatch. The
original evidence was not modified.

## Security qualification was rejected

Open-ended security review did not meet the qualification threshold:

- Two high-reasoning series produced zero schema-valid calls across three attempts each because
  output ended at the observed 8,192-token completion boundary while still reasoning.
- A medium-reasoning series produced schema-valid reports, but independent comparison found known
  critical misses and likely false positives.
- Targeted invariant probes produced useful hypotheses but were not reliably exact.

The harness therefore routes open security analysis and high or critical risk work to
`LEAD_ONLY`. This negative result illustrates why schema compliance and fluent explanations do
not establish semantic correctness.

## What these numbers do not prove

The results do not establish general coding ability, general security-review accuracy, suitability
for arbitrary repositories, or safety for autonomous actions. They do not transfer to another
model version, provider, quantization, prompt template, task class, adapter, or project without a
new qualification.

## Reproduction boundary

This public distribution includes selected summaries, hashes, schemas, policies, tests, and the
evidence verifier. It omits production source, raw private prompts, model weights, credentials,
and detailed operational evidence. The summaries allow readers to inspect the recorded scope and
results; they do not recreate private project inputs.

