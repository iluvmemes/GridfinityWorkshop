# Security policy

Report suspected vulnerabilities privately using [Report a vulnerability](https://github.com/iluvmemes/GridfinityWorkshop/security/advisories/new). Do not publish secrets or working exploits in public issues.

The current default branch and active development branch receive security fixes. Include affected versions, reproduction steps, expected impact and a suggested fix if available. The maintainer will assess the report and coordinate disclosure; no response-time guarantee is implied.

## Controls

Only `iluvmemes` administers this personal repository. Protected branches require a pull request, current passing Security checks and Dependency review, resolved review discussions and acceptable CodeQL results. No bypass actors are configured. Self-authored PRs do not require a second person's approval. CODEOWNERS requests the owner's review on contributions.

CodeQL analyzes Python, GitHub Actions and JavaScript/TypeScript when present, using extended security queries on pushes, pull requests and a weekly schedule. Dependabot checks action versions and the vendored JavaScript inventory. Dependency review rejects newly introduced vulnerabilities at any severity. GitHub secret scanning and push protection are enabled, together with Dependabot vulnerability alerts, security updates and private reporting.

Actions use full commit SHAs, read-only default tokens, no automatic PR approvals, and approval for all external fork contributors. Code scanning receives only the extra permission needed to upload results. Release jobs alone receive release write access.

## Vendored dependencies

`security/dependencies/package.json` and its lockfile inventory Three.js bundled by the workshop. They do not install packages into Fusion. Dependabot updates are proposals: updating this inventory alone does not update the shipped JavaScript. Regenerate the bundle, update its provenance/license as needed, and run the preview regressions before merging a Three.js update. The security check rejects a mismatch with the recorded bundled version.

Cloud scans do not exercise Fusion's modeling kernel or prove a print's mechanical fit. Native model/preview acceptance remains in `.agents/qa`.

## Availability and releases

Copilot Autofix is available with CodeQL on public repositories. Premium organization-only AI scanning and agentic remediation are not configured for this personal repository. GitHub did not enable non-provider secret patterns or validity checks when requested; supported-provider secret scanning and push protection remain enabled.

Protected integration branches require signed commits and squash merges. Release tags beginning with `v` cannot be edited or deleted, and tagged release workflows generate GitHub artifact provenance attestations. New releases must use a new version tag.
