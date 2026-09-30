## What changed

Describe the narrow behavior or documentation change.

## Evidence

- [ ] Added or updated deterministic tests where behavior changed
- [ ] Ran `python -m unittest discover -s tests -v`
- [ ] Rebuilt the package manifest
- [ ] Ran `python tools/verify_package.py`
- [ ] Confirmed no credentials, private prompts, model weights, or production evidence were added

## Boundary review

Explain whether this changes a schema, provider identity check, routing decision, evidence seal,
qualified task class, or authority boundary. Any broadened task class requires a new qualification.

