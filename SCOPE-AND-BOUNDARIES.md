# Scope and Boundaries

## Qualified lanes

### Local Devstral v4 reference

The local lane may choose one sealed source range for the v4 deterministic Python test-function extraction adapter. It is bound to the exact Devstral model digest and the separately sealed v4 qualification. This v5 package does not broaden that authorization.

### Cerebras bounded structural selection

The remote lane may choose among preregistered options in a strict JSON schema when all of the following are true:

1. Risk is LOW or MEDIUM.
2. The task is classified as `BOUNDED_STRUCTURAL_SELECTION`.
3. The input contains no restricted data or secret.
4. No external action or tool call is required.
5. A deterministic oracle can prove the selected outcome.
6. The exact project adapter has passed a repeated qualification series.
7. The model and provider match the pinned profile exactly.

The worker may explain a selection inside the schema, but its explanation is never approval evidence.

## Mandatory fail-closed gates

- Exact task, model, provider, profile, endpoint, schema, seed, and candidate ordinal recorded.
- Provider fallback denied and provider data collection denied.
- No tool definitions or tool authority supplied to the worker.
- Strict duplicate-key and non-finite JSON rejection.
- Original local schema validation after provider-compatible schema translation.
- `finish_reason` must prove a complete response.
- Candidate count must be complete and every candidate workflow-valid.
- Checkpoint resume may add a new attempt but never overwrite an earlier attempt.
- Retryable throttling honors `Retry-After`; semantic failures are not silently retried into a pass.
- Every request, response, proposal, receipt, profile, packet, endpoint record, and summary is hashed in a complete evidence seal.
- Independent evidence replay must reproduce the proposal from the stored response and reject any unsealed or altered file.
- A deterministic project oracle and separate lead approval remain mandatory.

## Lead-only work

- HIGH or CRITICAL risk
- Open-ended security review or threat-model adjudication
- Authentication, authorization, cryptography, trust roots, secrets, update trust, or privilege boundaries
- Arbitrary model-authored code patches or unrestricted editing
- Dependency, schema, database, build, installer, signing, deployment, publishing, cloud, VM, or Marketplace actions
- Any task requiring tools, credentials, network actions, or repository mutation
- Restricted data without an exact qualified local adapter
- A task without a deterministic oracle
- Any new project, rule, language, adapter, or transformation before qualification

Models may offer hypotheses in lead-only work, but the hypotheses receive no credit until deterministic tests reproduce them. A model is never the final judge of its own output.

## Promotion boundary

Qualification permits proposal generation in an isolated copy only. It does not permit direct writes to a primary repository, protected master, remediation worktree, VM, external provider, workbook, installer, or release artifact. Promotion requires independent evidence review, controlled application to the secondary worktree, fresh regression and security gates, exact source identity, and rollback evidence.
