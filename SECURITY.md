# Security policy

## Reporting a vulnerability

Please use GitHub private vulnerability reporting for the repository. Do not open a public
issue containing credentials, private model responses, unpublished source, or exploit details.

## Credential handling

The remote worker accepts an API key through an explicitly supplied local key file. The key is
read into memory, is not included in evidence, and completed evidence is scanned for accidental
disclosure. Never commit key files, `.env` files, raw production prompts, or unrestricted model
evidence.

## Scope

The harness produces proposals. It does not authorize model output, repository changes, tool
calls, deployments, releases, or security decisions. Review `SCOPE-AND-BOUNDARIES.md` before use.

