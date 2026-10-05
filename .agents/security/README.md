# GitHub security lockdown — 2026-10-05

Repository: https://github.com/iluvmemes/GridfinityWorkshop

## Verified access

`iluvmemes` is the only administrator and only collaborator. No pending invitations or deploy keys were present. The repository remains public.

## Enforced controls

- `master` and `feature/lid-generation`: PR-only changes, current passing Security checks and Dependency review from GitHub Actions, resolved discussions, CodeQL results with no security alerts or error-level findings, signed commits, squash-only linear history, no deletion or force pushes. No bypass actors. Zero mandatory extra approvals avoids blocking the sole maintainer's own PRs; CODEOWNERS requests the owner on contributions.
- All branches: no history rewrites. Release tags matching `v*`: no update or deletion.
- GitHub Actions: read-only default token, cannot approve PRs, all external contributors require workflow approval, full-SHA action pinning. Only GitHub-owned actions and the two explicitly listed existing release-action repositories are allowed.
- Extended CodeQL: Python, Actions and JavaScript/TypeScript when present, on pushes, PRs and weekly.
- Dependency review rejects new vulnerabilities at all severities. Dependabot vulnerability alerts/security updates and weekly action/npm inventory updates enabled. Three.js inventory is indexed by GitHub's dependency graph.
- Secret scanning and push protection enabled. Private vulnerability reporting and SECURITY.md added.
- Tagged release workflows now generate artifact provenance attestations. No release was published as part of this task; attestation execution awaits the next release.

## Verification

Initial CodeQL and security runs succeeded on both branches, including all three development-branch languages. Real PRs #2 and #3 passed dependency review, security checks and CodeQL, then merged through the normal API with rule-suite result `pass`; the master squash commit was verified signed. No admin bypass or disabled rules were used. Final alert queries returned zero open code, secret and dependency alerts. The nine local regressions also passed.

The first npm Dependabot run rejected an inventory in `.github/dependencies`. Moving it to `security/dependencies` through the protected PRs produced update PR #4. Actions updates produced PR #1. Both dependency upgrade PRs remain open for review; the bundled Three.js was not upgraded.

## Availability and limits

GitHub returned `disabled` for non-provider secret patterns and validity checks despite enable requests. They are not claimed enabled. Copilot Autofix accompanies public CodeQL by default; organization-only AI Scan/agentic remediation requires additional entitlements and was not enabled. References:

- https://docs.github.com/en/code-security/reference/secret-security/supported-secret-scanning-patterns
- https://docs.github.com/en/code-security/concepts/code-scanning/autofix-for-code-scanning
- https://docs.github.com/en/enterprise-cloud@latest/code-security/concepts/code-scanning/ai-powered-security-detections

Automatic approval review rejected a proposed no-force-push exception for Dependabot's topic branches because it weakens protection. The exception was not applied. A bot PR refresh that rewrites history may need a replacement branch/PR. Any future relaxation requires explicit authorization.

Cloud scans do not execute Fusion or validate printed fit. Native QA remains in `.agents/qa`. Earlier uncommitted workshop-integration files were preserved. Security-only commits are synchronized locally with the protected development branch.

`verified-settings.json` records read-back evidence and contains no secret values. `local-checks.txt` records local verification. Bootstrap command scripts are archived as `.py.txt` to prevent accidental reruns; they describe setup history, not a desired-state deployment tool.
