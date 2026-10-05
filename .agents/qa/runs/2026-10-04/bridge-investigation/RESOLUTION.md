# QA-003 bridge investigation — resolved as unconfirmed product finding

Date: 2026-10-04. Production code was not changed during this investigation.

## Evidence
1. Original production catalog handler was traced at entry/exit while a second observer recorded events. It received inspect and set _last_response successfully. The observer did not replace the handler.
2. Instrumentation was removed. The unmodified production handler completed a new inspect request.
3. The QA page returned an explicit ready acknowledgement containing its actual URL and harness version. Magazine HTML Create then succeeded through the original handler/native command, preserving an overlapping sentinel. Single Undo and Redo passed (generation about 0.219 s).
4. Hide/reopen returned the expected ready acknowledgement.
5. Add-in stop and run were executed in separate MCP calls; the catalog was opened by its registered command. Fresh production inspect returned successfully, with no JS errors. No observer or forwarding handler was installed on this fresh instance.
6. After the v6 harness acknowledged readiness, magazine HTML Create succeeded again (about 0.245 s). Its browser receipt contained creating then complete; Create was enabled again. See magazine-reloaded-roundtrip.json and the root create-magazine.json.
7. Fit-test HTML Create produced three pin coupons in a new design (about 1.469 s). Browser receipt again confirmed creating -> complete and enabled Create. See fit-tests-roundtrip.json and root create-tests.json.
8. Production HTML was restored and inspected before cleanup; final evidence is restoration.json. Only disposable QA documents were used.

## What was wrong with the previous conclusion
The previous harness changed palette HTML and dispatched subsequent actions without proving that the requested page and its handler had loaded. It then used shared _last_response/_last_creation fields, which may still represent a prior action. Missing or stale data under that protocol does not establish an add-in callback defect. The earlier output-wrapper stack overflow is independently recorded, but it does not explain every later missing response.

We did not reproduce a production callback failure with explicit readiness and completion checks, including a fresh reload. We cannot retrospectively assign every earlier symptom to one exact cause. QA-003 is closed as an unconfirmed product finding invalidated by insufficient test synchronization, with the corrected path now verified.

## Reusable correction
catalog-harness.js v6 implements qaPing (expected handler version + actual page URL + state) and qaReceipt (bounded production status receipts + current report). fusion-create-e2e.py request_ready clears stale state; prepare refuses to run until the expected version and matching URL are acknowledged. Completion requires native result plus browser receipt, not a visible panel or a fixed delay. Failure to receive the acknowledgement is a harness/transport readiness failure, not proof that a bin generator failed.

No workaround was added to production and no Fusion transport guards were changed. This verification does not claim manual mouse orbit/zoom coverage.
