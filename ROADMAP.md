# Roadmap

The roadmap prioritizes evidence quality over the number of supported models or tasks. Work is
accepted in small units that can be tested, reviewed, and rejected independently.

## Now: make the reference implementation easy to evaluate

- Add synthetic edge cases for each existing routing refusal.
- Improve Windows, macOS, and Linux quickstart verification notes.
- Add a machine-readable summary command for package and evidence verification.
- Document how to inspect a failed qualification without weakening the fail-closed result.

## Next: qualify one additional narrow task lane

The next adapter should have:

- one bounded task class;
- a deterministic oracle that does not ask another model to judge correctness;
- synthetic fixtures with tempting wrong answers;
- explicit abstention behavior;
- repeatable evidence and a negative tamper test; and
- no tool, publishing, deployment, or self-approval authority.

Good candidates include exact configuration extraction, selection from a preregistered option
set, or a transformation with a project-owned parser and invariant checks. Open-ended security
review remains outside worker qualification.

## Later: comparison and reporting

- Compare pinned model and provider identities on the same frozen case set.
- Export qualification summaries in a stable machine-readable format.
- Add longitudinal drift checks without treating old evidence as current qualification.
- Publish worked examples showing both accepted and rejected adapter proposals.

## How to contribute

Use the repository issue forms to submit a reproducible bug, adapter proposal, deterministic
oracle, or documentation improvement. A proposal is an invitation to test an idea; it does not
expand a qualified lane until its evidence passes independent review.

Starter work is labeled [`good first issue`](https://github.com/fusiontechstrategies/AI-Accuracy-Harness/labels/good%20first%20issue).

