# PR #17 focused independent re-review

Verdict: **PASS for the focused source, interaction and exact-artwork permission review. Latest-head Linux/Windows canonical CI remains required before merge.**

Reviewer: separate read-only Codex agent `/root/pr17_blocker_rereview`. Reviewed fixes over `d7dfd5c3ed3f9d9077b1a52a9608f28a546ab828`, including the follow-up working tree over `1055c5f090aacb0287d77c6fd5f2b791aca6dcea`, on October 10, 2026 Philippine time. No repository, Figma or GitHub edits were made by this reviewer; only temporary QA report/screenshot artifacts were saved.

## Three requested blockers

1. **Windows paths and frozen checkout bytes: source PASS.** `approved-board.test.mjs` imports `fileURLToPath` and uses `fileURLToPath(new URL('..', import.meta.url))` for Vite root. The new Windows job runs the existing canonical verifier with Python 3.12 and Node 22.18.0. The first Windows run exposed Git's LF-to-CRLF conversion of hash-bound SVGs. The follow-up `.gitattributes` rule `frontend/src/assets/figma/*.svg -text` narrowly prevents that conversion without weakening hash assertions or changing asset bytes. Actual new-head Windows success is still required.
2. **Replay: PASS.** `lastPlaybackRevision` records an explicit Speak/Replay attempt. Replay remains available for the same unchanged message after successful `idle`, Stop (`stopped`) or recoverable `error`, provided speech remains available. Actual word edits invalidate visibility using the existing monotonic revision. Rejected thirteenth taps preserve the actual unchanged message. Speech starts only through a native button's explicit `onClick`; no automatic replay or speech helper rewrite exists.
3. **Artwork permission: PASS based on the actual scoped author declaration and grant.** `ASSET-RIGHTS.md` records Robin's Figma authorship and the specific statement: "I, Robin, created these 43 SVG illustrations without third-party artwork and authorize their distribution with Tanaw's source code and application." The actual response supplied for this review is "Yes, record that statement". The record binds permission to all 43 exact hashes in `source-manifest.json`, including board, essentials, previews and utility icons. It preserves authorship/permission with the assets; does not invent a third-party license, broad relicensing or project-wide license; and explicitly keeps recognition/clinical validation separate and unverified. Pending old Figma metadata and earlier source scripts are not used as the clearance basis. No SVG bytes changed.

## Independent evidence

- Independent full `npm test`: **50 tests PASS**, zero failures. After the rights/manifest follow-up, independently repeated touched board/replay tests: **7 tests PASS**, zero failures. All 43 export hashes/root dimensions and all 32 canonical mappings pass.
- `git diff --check`: PASS. `git check-attr` confirms SVG `text: unset` and App `text: unspecified`.
- Independently reproduced Windows failure cause: original LF `imgGroup.svg` SHA-256 is `b2102fa5c1bd971ec1edf7d04fdb4bd422aef4e6c3d6d2d0b2dc85074e69ded0`; LF-to-CRLF yields `38d3c97ad96d0314e0df8e1f451cad23708ca718321a3946bb91047b8a1f1c53`, exactly the Windows failure. This supports the narrowly scoped EOL fix.
- Fresh independent Chrome actions used the actual App and unchanged Earl helper with synthetic browser events: initial 0/no Replay; Want → Eat → Apple → Speak count 1; completion retains Replay/count 1; explicit Replay count 2 → Stop retains Replay/count 2; explicit Replay count 3 → recoverable failure retains Replay/count 3; explicit Replay count 4 → Stop → Add No hides Replay/count 4. State transitions never start speech.
- Full-page evidence: `/private/tmp/tanaw-pr17-independent-replay-completed.png`, showing original selections, synthetic counter 1, visible Replay and synthetic QA disclaimer.
- `frontend/test/replay-check.html/.jsx` is a separate QA entry excluded from the production Vite entry. These synthetic events are not audible/offline certification or a recording-license assertion.
- Actual earlier CI run [37986296440](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/actions/runs/37986296440), on `1055c5f090aacb0287d77c6fd5f2b791aca6dcea`: Linux SUCCESS, Windows FAILURE before EOL correction. Do not represent that old Windows run as PASS. Latest-head rerun remains pending at report time.

## Scope and engineering quality

Small changes fix only the requested blockers and necessary Windows checkout evidence. No redesign, dependency additions, changes to card IDs/order, automatic speech, shared contracts, backend or Earl speech runtime. Native Replay is minimal/testable. The permission record states actual declaration and scope without claiming independent clinical recognition validation.

## Exact merge recommendation

**Source/rights re-review PASS. Wait for Linux and Windows canonical CI on the final PR head before recommending merge.** If both pass, these three requested review blockers are resolved and the small React checkpoint is suitable for Lead Architect integration. Preserve the author/permission record. Do not infer demo-ready audible/offline speech, clinical validation or completion of later AI work from this focused review, and do not merge autonomously.
