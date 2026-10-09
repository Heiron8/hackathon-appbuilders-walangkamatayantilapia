# PR #17 focused independent re-review

Verdict: **CHANGES REQUIRED — DO NOT MERGE.**

Reviewer: separate read-only Codex agent `/root/pr17_blocker_rereview`. Reviewed changes over `d7dfd5c3ed3f9d9077b1a52a9608f28a546ab828` on October 10, 2026 Philippine time. Reviewer made no repository, Figma or GitHub edits; this report and screenshot are temporary QA artifacts.

## Blocker findings

1. **Windows test path: code PASS, Windows execution pending.** `approved-board.test.mjs` imports `fileURLToPath` and uses `fileURLToPath(new URL('..', import.meta.url))` for Vite root. This resolves Windows drive/encoded-path semantics correctly. The new `verify-windows` job uses Python 3.12, Node 22.18.0 and the existing canonical `python scripts/verify.py --ci`, covering tests/build/backend/loopback verification. Actual Windows CI on the fix commit is still required; Mac testing is not Windows evidence.
2. **Replay: PASS.** `lastPlaybackRevision` records only explicit Speak/Replay attempts. Replay renders for the current unchanged message after `idle`, `stopped` or recoverable `error`, and only when speech capability remains available. Actual word changes invalidate its visibility through the existing monotonic revision; blocked thirteenth selections preserve the unchanged message. `ReplayButton` invokes speech only through `onClick`. No speech-runtime module was changed.
3. **Artwork redistribution: BLOCKING, NOT CLEARED.** `ASSET-RIGHTS.md` correctly records the absence of clearance for the exact 43 SVG exports bound by current manifest hashes, and keeps `redistribution_review` pending. Earlier monochrome scripts differ from current colored exports and cannot establish exact-export provenance/rights for all files. Native Figma components and export URLs are not redistribution permission. No complete actual author/permission declaration or verified compatible replacement is present. An honest audit record is useful but does not resolve the user's redistribution blocker.

## Independent verification

- Independent `npm test`: **50 tests PASS**, zero failures. New regression cases cover completed/idle, stopped, recoverable failure, explicit click count, first-playback exclusion, speaking exclusion and unavailable/current-message gating.
- `git diff --check`: PASS.
- Fresh independent Chrome UI testing used `frontend/test/replay-check.html/.jsx`: the real App with unchanged Earl speech controller and synthetic browser events. Initial count 0/no Replay; Want → Eat → Apple → Speak count 1; completion leaves idle/Replay with count 1; explicit Replay count 2 → Stop leaves Replay/count 2; explicit Replay count 3 → recoverable failure leaves Replay/count 3; explicit Replay count 4 → Stop → Add No hides Replay without another speech request. Thus state transitions themselves never request speech.
- Full-page proof: `/private/tmp/tanaw-pr17-independent-replay-completed.png`, showing original selected words, counter 1, visible Replay and synthetic QA disclaimer.
- QA fixture is a separate test HTML entry, not the production Vite entry. Synthetic evidence does **not** certify audible speech, offline device readiness or clip rights.
- Root-run build/canonical and exact-head Linux/Windows CI results are pending at this interim review. No pending check is represented as passing.

## Scope and quality

Small changes address the requested path/replay blockers without redesign, new dependencies, automatic speech, changes to canonical card IDs/order, or speech/backend ownership changes. Replay helper is minimal, testable and native-button based. QA fixtures and an explicit audit keep evidence separate from production capability claims.

## Exact merge recommendation

**DO NOT MERGE PR #17 until all 43 bundled exports have actual redistribution clearance or are replaced with verified compatible approved assets, and canonical Windows/Linux CI passes on the latest commit.** Code fixes 1 and 2 pass focused read-only review; unresolved artwork clearance remains a required blocker regardless of green CI. Request independent re-review of actual rights evidence/replacements before changing the overall verdict to PASS.
