# Contributing

Contributions should preserve the harness's fail-closed behavior and proposal-only boundary.

Before opening a pull request:

1. Add or update deterministic tests for the behavior being changed.
2. Run `python -m unittest discover -s tests -v`.
3. Run `python tools/verify_package.py` after rebuilding the package manifest.
4. Do not include credentials, private prompts, production evidence, model weights, or project
   source used during qualification.
5. Explain any change to schemas, provider identity checks, evidence sealing, or routing rules.

Changes that broaden a qualified task class require a new qualification. Existing results do
not transfer automatically to a new model, provider, adapter, project, or transformation.

