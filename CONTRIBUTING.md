# Contributing

Contributions should preserve the harness's fail-closed behavior and proposal-only boundary.

## Start with the right issue

- Report reproducible behavior with the bug form.
- Propose one bounded worker lane with the adapter form.
- Propose a mechanical grading method with the deterministic oracle form.
- Report unclear or missing guidance with the documentation form.

Read the [roadmap](ROADMAP.md) before proposing a broader task class. Questions about the
operating pattern belong in GitHub Discussions.

Before opening a pull request:

1. Add or update deterministic tests for the behavior being changed.
2. Run `python -m unittest discover -s tests -v`.
3. Run `python tools/verify_package.py` after rebuilding the package manifest.
4. Do not include credentials, private prompts, production evidence, model weights, or project
   source used during qualification.
5. Explain any change to schemas, provider identity checks, evidence sealing, or routing rules.

Changes that broaden a qualified task class require a new qualification. Existing results do
not transfer automatically to a new model, provider, adapter, project, or transformation.

## Small contributions

Issues labeled `good first issue` are intentionally scoped so a contributor can complete one
verifiable improvement without changing the authority boundary. A useful pull request should
solve the named issue, include the evidence requested by the template, and avoid unrelated
cleanup.

