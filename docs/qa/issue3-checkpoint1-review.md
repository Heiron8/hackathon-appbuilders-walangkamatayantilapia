# Issue #3 independent code and rendered QA

Verdict: **PASS for the first direct AAC frontend checkpoint**, after correction and independent re-review. This does not close the later sentence-inference checkpoint or certify integrated audible/offline speech.

Reviewer: separate read-only Codex agent `/root/tanaw_design_qa`. Reviewed current `task/issue-3` working tree over `d4d7e33` on October 10, 2026 Philippine time. No source, documentation, Figma or GitHub edits were made by this reviewer; only local QA artifacts and normal test/build outputs were created.

## Approved reference and scope

- [Heiron8 approval](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087693386), [independent design QA](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087806342).
- Existing approved Figma: [tablet](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=31-10), [desktop](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=31-6149), [phone](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=31-8062).
- Inspected App, CSS, Picture, message reducer, explicit speech profile, local pictogram manifests/assets, new tests, main entry, design docs and minimal product-verifier adjustment. Read architecture/UX contracts and review guidance. Backend, shared vocabulary/contracts, existing speech helper and dependencies are unchanged.

## Resolved findings

1. **Keyboard focus lost after Move/Remove:** positional keyed rows remounted. New deliberate post-update focus follows the moved word or adjacent Remove control. Fresh keyboard Enter test moved Apple word 3 earlier, producing Want/Apple/Eat and active `Move Apple, word 2, earlier`; removing Apple retained active `Remove Eat, word 2`.
2. **Empty editor exit lost focus:** removing every word then Done attempted to focus a disabled opener. Fresh re-review now focuses the board heading, with an evident focus ring, rather than BODY.
3. **School preview split inside a word:** phone 110px token rendered Schoo/l. Added to approved 160px preview width; fresh re-review shows one complete School label line.
4. Parent identified shared SSR/dev Vite-cache interference and narrow-nav/three-column Something else wrapping. Current render test uses an isolated temporary cache and cleans it. Fresh post-test page reload still renders all 32 cards with no console errors. Fresh 320px nav shows whole Conversation label with no horizontal overflow; phone Something else is two complete words/lines.

## Fresh independent evidence

- Actual Chrome rendering at CSS 390×844, 1024×768, 1440×900 and 320×640. No body horizontal overflow. Desktop has six columns, tablet four, standard phone three, narrow phone two. Tablet card width approximately154px; narrow cards approximately134px; all inspected visible desktop buttons met48px minimum target dimensions.
- All 32 canonical card IDs appear in exact shared-vocabulary DOM order. Local pictures load with zero broken images. Essentials use the same canonical IDs/picture exports and remain above the composer; phone board precedes optional assistance.
- Repeated taps append repeated words. Thirteen No taps leave exactly12; all12 editor rows exist in the independent scrolling list. Removing last word focuses the preceding word; message edits preserve fixed main vocabulary ordering.
- Clear opens a native modal with Keep message focused. Cancel preserves the selected word and returns focus to Clear. Explicit Clear message empties the message and focuses the board heading.
- Review preserves composer, selected pictures and essentials, deliberately reveals optional help, and marks original selected pictures. Conversation and Improve sentence remain disabled. No candidate is fabricated or automatically approved/spoken. Reducer tests cover invalidation of candidate/approved text/request on every accepted selection change.
- Default profile truthfully reports speech unavailable. No automatic speech start exists in App. Explicit `speakCards` receives a copied ordered snapshot; Stop audio is distinct from the Stop AAC card. Existing speech unit tests cover order/repeats, Stop, stale events, timeout/failure and truthful unavailability; audible UI playback is not claimed.

Independent local screenshots:

- `/private/tmp/tanaw-independent-react-phone-final.png`
- `/private/tmp/tanaw-independent-react-phone-review.png`
- `/private/tmp/tanaw-independent-react-tablet.png`
- `/private/tmp/tanaw-independent-react-desktop.png`
- `/private/tmp/tanaw-independent-react-narrow.png`

## Tests and provenance

- Independent `npm test` and `npm run build` both exit0 after the final fixes/profile change; `git diff --check` passes. The SSR asset/order test now has its own temporary Vite cache, so it does not invalidate the active browser dev build.
- 43 locally bundled SVG exports are hash-bound in the Figma provenance manifest; tests verify original root dimensions/bytes and mapping of all32 canonical IDs. A fresh scan found no script, event-handler, foreignObject or external-active references in these SVGs. Runtime rendering does not depend on expiring MCP URLs or emoji replacements.
- Symbol recognition and redistribution remain explicitly pending for these Figma exports. The separate Issue #5 QA asset hashes are not treated as recognition/license evidence for different Figma pictograms.
- `VITE_TANAW_SPEECH_PROFILE=loq-zira` is an explicit opt-in to only `Microsoft Zira - English (United States)`; default/unknown profiles supply null/empty clips. Tests verify the narrow opt-in. Independently read immutable [device evidence](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/blob/3fd47c076aad4c5ec4abeb2ef04bdc857eda8ca7/docs/qa/evidence/2026-10-10-loq-assets.json): Gab/Robin, LOQ/Windows11/Chrome154, local en-US voice, human-confirmed physical disconnection and audible Stop/replay/reload. Existing helper additionally requires the exact URI plus localService and English. This config neither enables fallback recordings nor verifies a different device or this newly integrated React UI.
- `scripts/verify_product.py` changes only the obsolete placeholder assertion to check the actual React mount/app module. Backend health, vocabulary proxy and other checks remain intact. Actual rendering was independently checked rather than inferred from that source-level assertion.

## Remaining gates

No blocking findings remain for this checkpoint. Integrated React audible speech on the explicitly configured LOQ device, offline restart/reload and approved asset redistribution/recognition require their own evidence before claiming demo readiness. Optional inference/approval/error runtime flows belong to the next approved checkpoint; disabled unavailable UI here is intentional. Browser viewport override was reset and ownership returned to root.
