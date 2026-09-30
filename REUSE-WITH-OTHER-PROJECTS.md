# Reuse With Other Projects

Qualification does not automatically transfer to another repository. Reuse the operating pattern, then qualify the new project's adapter and deterministic oracle.

## 1. Freeze the project boundary

Record the project name, exact source revision or source hash, allowed isolated work root, protected roots, forbidden paths, tool versions, test commands, scanner settings, exclusions, and rollback method. Do not point a worker at the primary repository.

## 2. Choose one narrow task class

Describe a single repeatable decision or transformation. Pre-register every allowed choice. Define what the worker is forbidden to change. If the result cannot be proved mechanically, keep the work lead-only.

## 3. Build the deterministic oracle first

The oracle should verify source identity, allowed change scope, syntax, formatting, scanner differential, targeted behavior, broader regression behavior, security invariants, and exact restoration. Add hostile tests that deliberately produce tempting but wrong worker answers. Prove that the oracle rejects them before invoking a model.

## 4. Select a lane

- Prefer the local Ollama lane when the exact task fits the qualified local adapter or data cannot leave the host.
- Use the Cerebras lane for non-restricted bounded structural packets that fit within a strict schema and have a qualified deterministic oracle.
- Route high-risk, security-sensitive, ambiguous, unrestricted, or externally acting work to the lead.

Run `select_lane.py` with a complete routing request and preserve its decision. Never mark an adapter qualified merely to obtain a faster route.

## 5. Seal the case plan

Use representative real project cases, edge cases, known-good controls, known-bad controls, malformed responses, collisions, timeouts, provider drift, and evidence tampering. Hash the plan before testing. For a new adapter, use at least three independent runs of every case and require zero unexplained escapes.

## 6. Qualify exact identities

For Ollama, record the exact model name and digest. For OpenRouter, record the exact model, provider, endpoint metadata, profile, and provider controls. A different digest, provider, quantization, template, context configuration, or task class is a new qualification target.

## 7. Preserve complete evidence

Store the input packet, request, raw response, validated proposal, deterministic evaluation, receipt, endpoint or runtime identity, summary, file hashes, and evidence seal. Preserve rejected and interrupted attempts. Never overwrite the original evidence or convert a failed run into a passing run by deletion.

## 8. Perform independent review

The author and worker do not approve the result. A different reviewer replays the evidence, attacks the deterministic oracle, verifies that protected state was untouched, and issues a scoped GREEN, HOLD, or RED decision.

## 9. Operate in shadow mode

Begin with proposals that are not applied. Compare worker decisions with the lead's independent decisions. Advance to isolated deterministic transformations only after the shadow series is clean. Apply to the secondary worktree only after independent approval and rerun all relevant gates there.

## 10. Monitor and revoke

Track first-pass accuracy, retries, deterministic rejections, escaped defects, model or provider drift, latency, cost, and reviewer disagreement. Any escaped defect, unexplained identity drift, weakened gate, or evidence-integrity failure suspends the lane until requalification.

## Minimum handoff package

A reusable project adapter should contain:

- project intake and protected-root declaration
- exact task and output schemas
- deterministic transformer, if any
- deterministic oracle and hostile tests
- sealed qualification case plan
- repeated qualification evidence
- independent review
- operating and rollback procedure
- package manifest and verification tool

The safe scaling mechanism is not a generally trusted model. It is a collection of small, independently qualified lanes whose outputs cannot bypass deterministic evidence and lead approval.
