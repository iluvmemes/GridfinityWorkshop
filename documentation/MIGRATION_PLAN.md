# Local workshop migration plan

Move the primary interface from Fusion palettes to a local Next.js application in this repository. Keep the existing Python generators and use Fusion's established local MCP connection for CAD execution. Retire the palettes when the core workflow meets the acceptance criteria below; full feature parity is not a prerequisite.

Status: planning baseline, 2026-11-11. Implementation has not started. The repository layout and work packages below describe the proposed implementation sequence.

## Decisions and scope

- Keep one repository and release the application and compatible Python generation package together.
- Run the application, project storage, preview, and Workshop MCP service locally. Bind services to loopback only. No hosted deployment, account service, external fonts, telemetry, or remote asset dependency is required at runtime.
- Start planning without Fusion running. Require Fusion only for native inspection, generation, and CAD export.
- Give manual controls and MCP tools the same validated operations, saved state, revision checks, and undo history.
- Freeze palette feature development. Limit changes during migration to preservation, necessary fixes, data export, and extraction of shared generation behavior.
- Retain existing generators for deferred features. Do not promise those features in the new interface before their acceptance checks pass.

Local deployment does not change the execution or data handling of a separately configured MCP client. Workshop itself requires no model service.

## Preserved baseline

Commit `b2a1b141701a75b388cc9b5f49e290bec28b9508` preserves the palette implementation, lettering, lid labels, colored exports, bundled font assets and licenses, preview improvements, and reusable QA tools.

The staged snapshot passed all 22 saved unit suites and release extraction checks covering 135 archive entries, Python compilation, local asset references, and 39 SMT presets. These are preservation checks, not a new live Fusion qualification. The dated report in `QA_RESULTS_2026-10-19.md` remains historical evidence.

Local model experiments, downloaded reference material, design critique notes, inspection dumps, and one-off export scripts remain outside this software baseline. Preserve them locally. They are not application dependencies or release inputs.

Recover the palette version by checking out the baseline commit into a separate directory and building its add-in archive. Avoid rolling the active checkout backward or overwriting the new application's data. Export embedded-browser favorites before changing or removing the legacy installation, because their storage can depend on its location.

## Core workflow required for retirement

| Area | Required before palette retirement | Deferred beyond retirement |
| --- | --- | --- |
| Projects | Create, name, save, reopen, duplicate, export, and import a local project; back up and restore its data | Advanced local project cataloging and bulk organization |
| Drawers | Named drawer dimensions and shallow/deep presets; grid placement of bins with bounds and overlap checks | Automatic packing, arbitrary tool silhouettes, and advanced layout optimization |
| Baseplates | Grid and drawer-fit modes, padding, solid/skeleton styles, magnet preset, print-bed limits, split layout and repeat-friendly print planning | New baseplate geometry families |
| Standard bins | Open and divided interiors, grid dimensions, explicit body-top height, optional standard stacking rim, press-fit base magnets | Magnet-channel interiors, custom blanks, clasp bins, cartridges, magazines, and fit tests |
| Preview | 3D orbit/zoom/fit, selected-object inspector, 2D drawer layout, dimensions, validation messages, and revision-labelled capture | Full CAD rendering fidelity and interactive face editing |
| Shared editing | UI and MCP read/write the same project; conflicts are visible; undo/redo works for both | Simultaneous independent generation workers and real-time collaborative merging |
| Generation | Generate the chosen project revision in an explicitly selected Fusion document, inspect the result, and export a basic STL in millimeters | Automatic regeneration of edited CAD, colored assemblies, batch export formats, and direct slicer control |
| Lettering and lids | Preserve existing implementation and saved settings | Dovetail lids, retention, lettering placement, font coupons, and colored lid exports in the new UI |

The core release deliberately has a smaller feature set than the preserved palette version. Unsupported legacy recipes remain recoverable and exportable; importing them must not silently drop fields or convert them into another family.

## Target architecture

Use a persistent local Node service as the owner of domain operations and SQLite storage. Serve the Next.js application locally, with its preview running in the browser. The HTTP UI API and Workshop MCP adapter call the same service operations. A lightweight stdio connector may connect MCP clients to the existing local service; it must not create a second independent project store.

The service is also an MCP client to Fusion. Both the Generate button and the Workshop generation tool call the same job operation; no conversational client is needed to use the application manually. Fusion executes packaged Python through a small, versioned entry point with explicit parameters and results. Keep the native command handlers needed for undo and document interaction even after palette UI is removed.

| Proposed location | Responsibility |
| --- | --- |
| `apps/workshop/` | Next.js routes, React controls, project navigation, and local browser interface |
| `apps/service/` | Local launcher/service, HTTP API, event stream, SQLite persistence, generation queue, and shutdown |
| `packages/domain/` | Versioned recipe schemas, project rules, pure layout calculations, operation definitions, and validation |
| `packages/preview/` | Existing Three.js geometry adapted behind a renderer interface; later React Three Fiber components where useful |
| `packages/mcp/` | Workshop tool/resource definitions and connector to the shared service |
| `integrations/fusion/` | Fusion MCP client, capability checks, packaged Python entry point, and native command lifecycle |
| `workshop/` | Existing Python generators and assets during extraction; palette files removed only at cutover |
| `tests/fixtures/` | Neutral reference recipes, expected layouts, migration cases, and cross-language validation fixtures |

Do not move every existing file at the start. Introduce the generation boundary in place, preserve relative asset loading, then move modules only when their consumers and release packaging are covered. The existing add-in builder includes the entire `workshop` directory, so retirement requires an explicit packaging change.

Start by wrapping the current Three.js renderer. A wholesale preview rewrite is not required for the first shared workflow. Separate recipe state from transient camera, hover, drag, and selection state. Commit a drag as one edit on completion; intermediate visual motion need not write the database.

## Data and operation contracts

Persist stable project, drawer, and item IDs; a schema version; an integer project revision; normalized recipes; placement; printer/fit profiles; and generation references. Store database backups and exported project files in a stable local data directory outside the installation and source checkout. Record the data schema version and back up before migration.

Every durable mutation supplies the expected revision and a unique operation ID. Validate and apply it transactionally, advance the revision, append the undo/event record, and notify subscribed browser sessions. Repeating the same operation ID returns its recorded result. A stale revision returns a conflict with the current revision rather than overwriting another edit. Undo and redo create new revisions; they do not rewind the revision counter. Serialize writes in the first release.

The browser subscribes to a resumable event stream. On reconnect, it either catches up from its last event or reloads the authoritative snapshot. A preview capture includes its project revision, rendered revision, selected item, and camera. Return a clear unavailable/stale result when the browser is closed or has not rendered the requested revision.

Initial MCP operations cover project inspection, recipe/layout updates, validation, undo/redo, view selection, preview capture, generation submission, and job status. Use bounded domain inputs rather than exposing arbitrary code execution through Workshop.

### Dimensions and preferences

- Use millimeters in the persisted recipe and operation contract. Convert to Fusion's internal units only at the integration boundary.
- Default grid-based items to four standard magnet positions per 42 mm cell, with 6.08 mm hole diameter and 2.4 mm depth. Disabling or changing this preset requires an explicit recipe choice.
- Default drawer B/C bin body tops to 21 mm and A/D/E/F body tops to 35 mm, measured from the bottom of the feet. Track raised lettering and total assembled height separately.
- Represent cavity depths explicitly so changing body height preserves pocket depth. Validate the remaining floor thickness and reject impossible combinations.
- Translate legacy `height` values in 7 mm units explicitly. Do not silently reinterpret an old height or alter imported geometry to adopt new defaults. Import should identify differences and offer a deliberate update.
- Keep Python manufacturing validation authoritative before generation. Mirror necessary rules in TypeScript for responsive planning and test both against shared neutral fixtures to prevent drift.

The existing height-driven cavity construction needs explicit verification during extraction; it is not assumed to satisfy the pocket-depth rule already.

## Generation lifecycle

Freeze the normalized recipe, recipe hash, project revision, generator version, target document, and job ID at submission. Later project edits affect the preview but not the running job. Mark the CAD result as belonging to an older revision when appropriate.

Use durable job states: queued, running, succeeded, failed, cancelled, and outcome unknown. Execute one Fusion mutation job at a time. Recheck the target document, required capabilities, and native command readiness immediately before execution. Never fall back to whichever document happens to be active.

Record a job marker on generated components and retain result identifiers plus measurements. A transport timeout or service restart after dispatch produces an unknown outcome until inspection reconciles the marker and document state. Do not retry an uncertain mutation automatically. Promise duplicate prevention where the persisted operation/job record proves it; do not claim unconditional exactly-once execution across crashes.

Cancellation is guaranteed only before dispatch. After execution starts, show the actual supported behavior. Preserve native Fusion Undo/Redo for CAD and distinguish it from Workshop recipe undo. If a generated component is undone, deleted, or its document closes, re-inspect before claiming the result is still available.

## Ordered implementation work

| Milestone | Deliverables | Exit evidence |
| --- | --- | --- |
| 0 Preserve | Reviewed baseline commit, neutral metadata/privacy check, unit and release checks, recoverable legacy snapshot | Baseline pushed; local-only exclusions documented |
| 1 Define and extract | Recipe/operation schema, height/depth conversion rules, stable Python generation entry point, native MCP invocation contract | One standard bin generated without a palette; intended document, magnets, height, pocket depth, solid health, and native undo verified in a disposable design |
| 2 Establish local state | Local service and Next.js shell, SQLite migrations/backups, shared operations, event subscription, Workshop MCP adapter | Manual and MCP edits converge; stale writes rejected; save/reopen and backup restore pass with Fusion closed |
| 3 Complete a vertical slice | Standard-bin editor and existing preview wrapper, selection/camera tools, preview capture, job queue and status | Manual edit, MCP edit, visible update, undo, reload, generation of the same revision, and basic STL export all pass |
| 4 Complete core scope | Baseplates, divided bins, drawer presets/layout, overlap checks, splitting/print plan, legacy import/export | Core feature matrix passes; invalid layouts cannot dispatch; imported core recipes retain intended dimensions |
| 5 Qualify distribution | Bundled local runtime, startup/stop behavior, installation/data separation, version handshake, repair/recovery guidance | Clean Windows launch without a development server or separately installed Node; planning with Fusion closed; restart, busy-document, and disconnect checks pass |
| 6 Retire palettes | Switch default launch/release, remove palette runtime and obsolete UI checks, retain generators/native commands and migration data | Retirement checklist complete; legacy restoration documented; no palette needed for any core workflow |
| 7 Extend | Port deferred families and fit workflows, followed by lids/lettering/colors and additional export formats | Each feature has its own recipe, preview, CAD, persistence, and shared-edit acceptance checks |

Milestones are ordered by dependencies, not calendar promises. The next implementation task is milestone 1. Its first deliverable is a small callable generator boundary and a disposable-design test, before any broad UI rewrite.

## Retirement checklist

- [ ] All core workflows run from the standalone application and Workshop MCP, with palettes closed and their registration disabled.
- [ ] Manual edits and MCP edits share one project revision and undo history; refresh and reconnect preserve the latest accepted state.
- [ ] Preview capture matches the requested revision or reports that it cannot do so.
- [ ] Baseplate and standard-bin geometry matches reference recipes for dimensions, body tops, cavity depths, magnet locations/diameters/depths, solids, and feature health.
- [ ] Invalid settings and stale operations cannot mutate Fusion; unrelated bodies and documents remain unchanged.
- [ ] Generation and basic STL export work without a conversational client; native undo/redo behaves as documented.
- [ ] Timeout, duplicate submission, app restart, Fusion restart, closed target document, and active-command conflicts have tested outcomes without silent duplicate geometry.
- [ ] Favorites and fit settings can be exported before removal and imported with validation. Unsupported recipes remain intact and clearly labelled.
- [ ] A fresh Windows installation can launch, save, reopen, back up, restore, connect to Fusion, and stop cleanly using bundled runtime assets.
- [ ] Deferred features are listed in the release notes; the preserved palette version can be restored from its baseline without overwriting project data.
- [ ] Current README, release packaging, startup registration, and tests describe the standalone product. Retired UI files are recoverable through Git rather than shipped in a permanent archive directory.

## Validation and remaining decisions

Reuse existing pure layout/preview tests and native geometry checks. Add tests around observable contracts: revision conflicts, shared undo, persistence, import preservation, reconnect, job reconciliation, document isolation, and representative exports. Use disposable Fusion designs and distinguish fresh native evidence from historical reports. Physical print fit remains separate from software geometry checks.

Resolve the following during their assigned milestones, recording the outcome before depending on it:

1. Milestone 1: the exact native MCP tool and return contract used to invoke the packaged Python entry point, including command execution and busy-state behavior. The local connection is established; this is integration qualification, not transport discovery.
2. Milestone 2: the SQLite driver and process boundaries for the packaged Windows runtime. Default to one authoritative service and one shared operations package.
3. Milestone 4: the legacy storage export method and handling of recipes whose requested height/depth combination cannot be represented without change.
4. Milestone 5: portable launcher versus installer. Default to a portable distribution first, with the runtime bundled and data stored separately. Verify operation without runtime downloads after installation.

Before committing any milestone, apply the root privacy requirements to content, filenames, fixtures, generated outputs, commit messages/trailers, and effective author/committer identities. Preserve required third-party license notices and exclude local evidence containing personal paths or session details.
