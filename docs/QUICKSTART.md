# Quickstart

This walkthrough exercises the routing and verification controls without contacting a model.

## Requirements

- Python 3.12 or newer
- Git, if cloning from GitHub

The included router, tests, and verification tools use only the Python standard library.

## 1. Verify the package

From the repository root:

```bash
python -m unittest discover -s tests -v
python tools/verify_package.py
```

The test run should report 18 passing tests. The verifier should report a verified package and
the manifest hash recorded in `PACKAGE_SHA256SUMS.sha256`.

## 2. Route a bounded remote task

```bash
python select_lane.py examples/remote-bounded-routing-request.json
```

The result admits the exact remote lane with `ADMITTED_PROPOSAL_ONLY`. It also states that tools,
repository mutation, and semantic approval are unavailable.

## 3. Route restricted data locally

```bash
python select_lane.py examples/local-ollama-routing-request.json
```

The result admits the local lane because the request declares restricted data, the exact local
adapter is qualified, and a deterministic oracle is available.

## 4. Observe a fail-closed decision

Copy a routing example and change `risk_tier` to `HIGH`:

```json
{
  "schema_version": "fusion.hybrid-routing-request/v1",
  "task_id": "EXAMPLE-HIGH-RISK",
  "task_class": "BOUNDED_STRUCTURAL_SELECTION",
  "risk_tier": "HIGH",
  "contains_restricted_data": false,
  "external_action_required": false,
  "deterministic_oracle_available": true,
  "local_adapter_qualified": false,
  "remote_adapter_qualified": true
}
```

The selector returns `LEAD_ONLY` and `NOT_ADMITTED_TO_WORKER`. A qualified adapter does not
override the risk boundary.

## 5. Inspect the evidence controls

- `qualification/EVIDENCE-INDEX.json` binds each selected summary to a SHA-256 digest.
- `qualification/tamper-negative-test.json` records an isolated proposal mutation that the
  verifier rejected.
- `verify_evidence.py` replays stored response material and checks the sealed inventory.

## 6. Before adding a project

Do not mark a project adapter qualified based on these demonstration cases. Follow
`REUSE-WITH-OTHER-PROJECTS.md`: freeze the boundary, build the deterministic oracle first,
create hostile cases, run repeated qualification, and obtain independent review.

