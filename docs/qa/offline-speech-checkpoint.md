# TANAW-04 / Issue #5 checkpoint and read-only review

Owner: GabDeGuz. Branch: `task/issue-5`, based on reviewed main `d26c959`.
Live Issue #5 was read in full and exclusive ownership/status reread through
`python scripts/claim_task.py 5`: OPEN, only GabDeGuz, `status:in-progress`.
Architecture is approved/released. Live task readiness permits standalone speech now.
The user's current instruction requires this existing repository and one task branch;
it supersedes historical separate-worktree wording. No extra worktrees were created.

## Checkpoint scope and evidence

- `frontend/src/speech/index.mjs`: standalone speech boundary, local-only synthesis,
  ordered card playback, capability/error state, stop/replay via explicit calls,
  cancellation/stale-event protection and cleanup.
- `frontend/src/speech/speech.test.mjs`: deterministic browser-API fixture tests.
- `frontend/src/speech/README.md`: integration interface and validation bounds.
- `docs/qa/speech-check.html`, `speech-probe.mjs`, `serve-speech-check.py`: temporary
  loopback-only manual check with no product UI or manifest edits. Server exposes
  only the QA page/module, speech module and optional canonical vocabulary.
- This file: verification, all-laptop readiness matrix, remaining gates, review handoff.

Verified October 9, 2026, on this checkout:

| Check | Evidence | Result / limit |
| --- | --- | --- |
| Identity and task | `gh api user --jq .login`; assigned issue list; full Issue #5; Issues-first helper | GabDeGuz, exclusive owner, existing In Progress reused |
| Git synchronization | `python scripts/project_sync.py` with network access | ALREADY CURRENT; main was clean before branch preparation |
| Node | `node --version` | v24.18.0 |
| Python | `python --version` | 3.13.15 |
| Native Windows voice inventory | `System.Speech.Synthesis.SpeechSynthesizer.GetInstalledVoices()` outside sandbox | Microsoft David Desktop and Microsoft Zira Desktop, enabled en-US; does not prove browser availability or playback |
| OS version | `System.Environment.OSVersion.VersionString` | Windows NT 10.0.26200.0; not the misleading legacy product-name registry string |
| Speech tests | `node --test frontend/src/speech/speech.test.mjs` | PASS: 18/18; mocks only |
| JS parsing | `node --check frontend/src/speech/index.mjs`; `node --check docs/qa/speech-probe.mjs` | PASS |
| Canonical repository verification | `python scripts/verify_workspace.py` | PASS: structure, workspace tests (1 skip), secret scan; not product/offline evidence |
| Real browser automation | Browser inventory empty; Chrome session unavailable | NOT VERIFIED; manual browser check required |
| Canonical vocabulary | `shared/vocabulary.json` absent on current main | Integration dependency on Heiron8/TANAW-01; no duplicate generated here |
| Bundled clips/symbols | No assets supplied in this checkpoint | NOT READY; no silent/dummy recordings or invented provenance |

The temporary server was checked with real loopback HTTP requests: page, probe and
speech module returned HTTP 200 with correct MIME types; absent vocabulary, `.git/config`,
`.env` and a traversal attempt returned HTTP 404. Source parsing passed after the final
code changes. This evidence does not claim an integrated product, real card playback,
or disconnected speech PASS.

## Every team laptop must pass independently

GabDeGuz confirmed that **all team members' laptops must be ready**. Evidence from
one machine cannot approve the others. Fill the matrix only from real witnessed
checks on each member's actual laptop/browser; record date/time and witness.

| Member | Laptop / OS / browser version | Local voice / URI | Physically disconnected sentence + stop/replay | Disconnected restart/reload | 32 real clips + ordered playback | Witness / evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Heiron8 | Not supplied | Not verified | Not verified | Not verified | Missing/unverified | Pending | NOT READY |
| RobinKielll | Not supplied | Not verified | Not verified | Not verified | Missing/unverified | Pending | NOT READY |
| LadlopezGit | Not supplied | Not verified | Not verified | Not verified | Missing/unverified | Pending | NOT READY |
| GabDeGuz | Windows build 26200 observed; browser not supplied | Native David/Zira observed; browser URI unverified | Not verified | Not verified | Missing | Pending audible/browser witness | NOT READY |

On each laptop:

1. Obtain this reviewed checkpoint through the team's normal delivery/integration
   process; Python and a supported installed browser are required for the QA page.
2. Run `python docs/qa/serve-speech-check.py`, open `http://127.0.0.1:8765`, record
   laptop, real OS/browser version, local English voice name and exact URI.
3. Physically disconnect Wi-Fi/Ethernet. Reload the page from the loopback server.
   `navigator.onLine` is only a hint; it cannot certify physical disconnection.
4. Explicitly Test candidate sentence. Hear the complete sentence. Test Stop while
   speaking and Replay from the start. Check that a Stop communication card will
   remain a selected word when UI is integrated, distinct from Stop audio.
5. Only the actual human witness checks the confirmation box. Test exported
   `speakText`, then stop/replay it explicitly. Copy evidence and identify witness.
6. Restart browser/server while disconnected, reload and repeat. No completion
   event alone proves audible sound. Missing/remote-only voice is a P0 blocker.
7. Once assets exist, audit all canonical WAVs: exact label, non-silent intelligible
   recording, speaker/source, license/consent and redistribution evidence; exact
   `/audio/en/<id>.wav` names. No unverified generated Microsoft voice recordings
   are bundled or presented as licensed fallback. Audit symbols' sources/licenses.
8. After RobinKielll's design-approved integration and shared vocabulary arrive,
   test Want → Eat → Apple, repetitions/corrections, explicit speech, model stopped,
   backend inference failure in an already loaded page, and truthful fallback/errors.
   Recheck all laptop rows against the actual integrated commit/build.

## Independent read-only review package

**Speech-code reviewer: RobinKielll. QA/evidence reviewer: Heiron8.**
Reviewers read these seven new files without editing this branch. For untracked files,
`git diff` alone is insufficient; use `git status --short`, read the listed files,
and rerun the Node tests and repository verifier. Do not stage/commit merely to
make the diff visible. Compare with Issue #5 and `docs/architecture/contracts.md`.

Review correctness and simplicity, exact local-voice pinning, no automatic speech
or text-to-card substitution, selection order/duplicates, 12-card bound, no remote
audio paths, cancellation/replacement races, failure/timeout cleanup, subscriber
state and integration usage. Verify scope excludes UI/state/styles/manifests/shared
ownership. Browser audition remains separate from production verification. Check
the text/watchdog bounds and accept or request a correction before integration.

Return **PASS** or **CHANGES REQUIRED**, with reviewer identity, scope, check time,
and evidence. Code-checkpoint PASS does not complete the issue's real-device/asset/
integrated-product acceptance criteria. GabDeGuz cannot independently approve this
implementation. No agent delegation or reviewer impersonation is inferred.

**Current review: PASS reported by GabDeGuz in the October 9, 2026 commit request.**
The user explicitly confirmed that independent PASS is complete and authorized a
local commit. Reviewer identity, review time and a separate review artifact were not
supplied in that confirmation; no reviewer attribution is inferred. All seven files
matched the prepared review ZIP before this review-status update. This records the
human's confirmation, not agent self-review or runtime/asset readiness. Do not mark
Issue #5 complete from this checkpoint. No push is included in this commit request.

A local review ZIP and patch are prepared at `reports/tanaw-04-review.zip` and
`reports/tanaw-04-review.patch` (ignored generated artifacts). The ZIP contains exactly
the seven scoped source/evidence files, no Git metadata or identity/credentials.
The package was prepared before this review-status update. No automated sending
was performed; it remains a snapshot of the submitted code and original evidence.

Remaining dependencies: Heiron8 supplies canonical vocabulary and agreed asset
names; real licensed/team recordings/symbols; local voices on all laptops;
RobinKielll integrates only after design approval; final fresh setup/demo evidence
requires the integrated build. Suggestions remain disabled behind their separate gate.
Feature freeze October 10 06:00, demo-ready 08:00 Philippine time (UTC+08).

Web API implementation reference: [MDN localService](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService)
and [Web Speech specification](https://webaudio.github.io/web-speech-api/#tts-section).
