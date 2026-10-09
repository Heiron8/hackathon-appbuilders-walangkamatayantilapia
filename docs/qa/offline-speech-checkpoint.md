# TANAW-04 / Issue #5 checkpoint and read-only review

Owner: GabDeGuz. Branch: `task/issue-5`, based on reviewed main `d26c959`.
Historical sections below retain their original verification counts. Current
PR #15 acceptance checkpoint: 47 frontend tests (31 controller, six assets/human
records, seven QA state regressions, three foundation); seven backend tests. The
current branch is `task/issue-5-assets`. See the latest acceptance update below.
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
| Heiron8 | Laptop unavailable this session | Pending | Pending | Pending | Pending | Pending | PENDING - not tested |
| RobinKielll | Laptop unavailable this session | Pending | Pending | Pending | Pending | Pending | PENDING - not tested |
| LadlopezGit | Laptop unavailable this session | Pending | Pending | Pending | Pending | Pending | PENDING - not tested |
| GabDeGuz | LOQ / Windows 11 supplied; Chrome 154 UA; build 26200 and Chrome 154.0.8037.58 separately observed | Microsoft Zira - English (United States); URI identical, en-US, localService true in supplied JSON | Prior human-reported PASS; physical-disconnection attestation true, initial browser hint true | Prior self-reported Zira restart PASS; bundled reload/restart self-reported PASS; combined restart details pending | 32 WAV labels + 32 pictures human-recorded PASS; bundled sequence self-reported PASS | Earlier asset witness Gab / Robin; follow-up JSON repeats same session; manually entered fallback report Gab | PARTIAL - assets PASS; validated fallback detail/device/integrated gates pending |

On each laptop:

Only GabDeGuz's laptop is available in the current session. The other three rows
remain PENDING, never inferred PASS. Use the [current-laptop checklist](current-laptop-speech-checklist.md)
and return its results form before recording any actual offline/audio PASS.
All-laptop and integrated-product readiness remain open under Issue #5.

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

**Previous checkpoint review: PASS reported by GabDeGuz in the October 9, 2026 commit request.**
The user explicitly confirmed that independent PASS is complete and authorized a
local commit. Reviewer identity, review time and a separate review artifact were not
supplied in that confirmation; no reviewer attribution is inferred. All seven files
matched the prepared review ZIP before this review-status update. This records the
human's confirmation, not agent self-review or runtime/asset readiness. Do not mark
Issue #5 complete from this checkpoint. No push is included in this commit request.

## PR #12 corrective checkpoint — October 10, 2026

The requesting owner relayed an independent **CHANGES REQUIRED** review, superseding
the earlier PASS for PR #12. The two blockers were explicit card fallback after
synthesis failure and playback starting after Stop/dispose from state observers.

- Failed synthesis (error, timeout, synchronous browser failure) is disabled for
  this controller. Complete audited clips remain available through a subsequent
  explicit `speakCards` call; failed full text never starts card playback itself.
  Reinitialize only after checking the local voice again.
- Pending playback is registered before startup notifications. Stop/dispose from
  either notification settles it as stopped before creating utterances/media/timers.
  Disposed controllers cannot restart playback. Error results are captured before
  notifying observers, so an observer's Stop cannot erase the caller's error.
- The merged Issue #1 foundation is included in the existing branch. Its canonical
  32-card vocabulary is exercised by the speech tests, including exact clip paths
  and repetitions. Shared speech type declarations now match the helper's result,
  playback/error and capability-detail shapes; API/vocabulary contracts are unchanged.
- `frontend/package.json` includes speech tests in `npm test`, which the existing
  canonical product verifier and CI already invoke. No dependency versions changed.

Verification: 31/31 deterministic speech tests and source parsing PASS on this
checkout. `python scripts/verify.py --ci` PASS: harness tests (one skip), secret
scan, 34 frontend tests including speech, production build, dependency compatibility,
seven backend tests and real loopback startup/proxy/static/reload/backend-stop checks.
Independent read-only Codex re-review: **PASS**, `/root/speech_rereview`, October 10,
2026 at 00:47 UTC+08. The reviewer independently ran the full canonical verifier
before the final error-snapshot correction and reran all 34 frontend tests after
reviewing that correction. No blocking or nonblocking findings remain. The
implementer reran the full canonical verifier after the final source change: PASS.
This Codex review is not attributed to RobinKielll/Heiron8 and does not replace
their human GitHub review. The verified correction is authorized for commit/push
to the existing PR #12; no merge is authorized by this checkpoint.
Issue #5 remains open/In Progress for real offline/device/assets/integrated QA.
No fixture audio or browser events prove audible speech or asset readiness.

## Issue #5 asset/offline continuation — October 10, 2026

PR #12 merged as `b60a177`. Clean main was safely synchronized using Project Sync,
then `task/issue-5-assets` was created in the same existing repository. No extra
worktree/clone and no canonical vocabulary or Robin UI changes were made.

**Actual human report:** Asked for disconnected exported `speakText`, Stop,
Replay and browser/server restart outcomes, GabDeGuz replied “pass”, then identified
“Microsoft mark” as the tested voice. Record this as a self-reported PASS for those
listed checks on the current laptop, not an automated audible observation or
independent QA approval. Exact voice URI, language/localService, test time, page
Evidence JSON and individual outcome detail remain unsupplied. Do not silently
pin a voice URI or mark all speech/asset/integrated requirements complete.

Read-only machine inventory observed Windows build 26200, native David/Zira
Desktop en-US and Chrome product version 154.0.8037.58. Native voice enumeration
does not enumerate all browser/OneCore voices and does not contradict the user's
reported Mark choice. Browser automation stopped because its policy guard could
not confidently determine the current URL; no alternate UI automation was used.

**Prepared assets:** 32/32 canonical WAV candidates, default eSpeak NG 1.52.0 en-us
formant voice, rate 145, mono PCM16 22,050Hz; 32/32 original SVG picture candidates.
No Microsoft-generated clips, MBROLA voices, third-party pictograms or remote
runtime assets. Source/settings/license and per-file hashes are in
`frontend/public/speech-assets.json` and `frontend/public/asset-licenses/`.
The pack is distributed under GPL-3.0-or-later with source/recipe notices.
Human audible-label audits: 0/32 recorded. Human picture-recognition audits:
0/32 recorded. Synthetic speech quality and semantic recognition remain open.

**Verification:** `python scripts/verify.py --ci` PASS with 37 frontend tests,
seven backend tests, production build, dependency compatibility, loopback smoke,
harness tests (one skip) and secret scan. All 32 WAVs have bounded non-silent PCM;
all 32 SVGs parse as XML and were rendered as a contact sheet for inspection.
Live loopback checks on port 8770 verified all 64 exact asset bytes/MIME types,
and denied private/traversal/unknown/query paths. These are structural/delivery
checks, not audible/disconnected/recognition PASS.

**Live QA:** The updated server at `http://127.0.0.1:8770` offers editable text,
card order/repetition/replay, explicit error checks, per-card WAV/picture audit,
and human-gated clips-only configuration. The existing 8765 test server was
preserved. Checkbox confirmation is local-session human testimony; it does not
persist or approve another laptop. Re-audit and retest after disconnected restart.

Independent read-only Codex review of this continuation: **PASS**,
`/root/asset_rereview`, October 10, 2026, 02:22 UTC+08. The reviewer independently
ran the full canonical verifier (37 frontend tests, seven backend tests), checked
all 64 live asset responses and denied routes, inspected all SVGs/contact sheet,
and confirmed all 67 pack files reach the static build with exact bytes. The
sole nonblocking finding was a stale dependency paragraph; it was corrected and
the reviewer confirmed PASS with no outstanding findings. This approves the code
and candidate checkpoint, not human audible/recognition/offline acceptance, and
is not attributed to RobinKielll or Heiron8. Issue #5 stays
OPEN/In Progress. The other three laptops remain PENDING; final integrated
Want -> Eat -> Apple -> Review -> Speak with Ollama stopped waits for Robin's
design-approved UI/build. No PR merge is authorized by this checkpoint.

Before PR publication, a portability check found that Windows-generated CRLF
SVG hashes differed from Git's committed LF bytes. Generation now writes LF and
`.gitattributes` pins SVG/manifest line endings; all 32 symbol hashes were corrected
to the actual committed bytes. Drawings and WAVs are unchanged. Independent
read-only re-review by `/root/asset_rereview`: **PASS**, October 10, 2026,
02:25 UTC+08, with full canonical verification and all 64 final-build asset hashes
checked. A regression rejects CR in SVGs. No outstanding review findings remain.

**Current laptop follow-up:** GabDeGuz reported Finished, Go and Milk pictures
missing on the 8770 QA page and requested Microsoft Zira. Direct loopback checks
returned HTTP 200, correct SVG MIME, exact disk bytes and valid XML for those
three pictures; the 32-symbol contact sheet renders them correctly. The browser
display failure was not reproduced by these checks. After asking the tester to
reload/retry those pictures and confirm Zira selection, GabDeGuz replied "it is
okay now" on October 10. Record the named picture display/voice-selection checks
as self-reported recovered, without inferring all-symbol recognition or Zira
audible/offline PASS. The original display failure's cause remains unconfirmed.
QA now reports image-load failures, offers fresh-image Retry/direct links,
and prevents recognition confirmation for loading/failed images. Late/stale image
callbacks cannot confirm a replacement picture.

Microsoft Zira is now the preferred QA candidate when reported as a local English
voice. Missing Zira is reported without silently choosing Mark. An explicit tester
choice is retained; selecting Zira does not verify it or start speech. The previous
Mark report stays historical. At this QA-control checkpoint, Zira URI/audible/
offline/Stop/Replay/restart checks were pending; see the subsequent human result
below. Existing fallback WAVs remain licensed eSpeak recordings, not Zira
recordings. Full canonical verification PASS: 37 frontend tests, seven backend
tests, production build, dependency compatibility, loopback smoke, workspace
checks and secret scan. QA control fixture checks pass; they do not establish
audibility or offline PASS. Independent read-only Codex review:
**PASS**, `/root/asset_rereview`, October 10, 2026, 02:37 UTC+08, no outstanding
findings. The reviewer independently checked the frontend/QA fixtures, parsing,
diff and exact three-symbol HTTP/XML delivery, including extra remote/non-English/
disappearing-voice and stale-picture callback cases. This approves QA preparation
for the existing draft PR #15; Issue #5 stays open and no merge is authorized.

**Zira human result — October 10, 2026:** Asked whether Zira speech, Stop,
Replay and disconnected restart all passed or whether any failed, GabDeGuz
replied "it all pass". Record **PASS, self-reported by the current laptop tester**
for these four named checks. This is actual human testimony, not a result inferred
from unit tests, browser events or the agent listening. No independent witness
was supplied. Exact voice URI/language/localService, Evidence JSON, helper result
details, individual test times and tested commit remain unsupplied. The prepared
QA code at the time of this report is `63bdd51`; that is not an independently
confirmed tested revision. Do not copy Mark's URI or invent Zira metadata.

This report does not cover all 32 WAV label auditions, all 32 symbol-recognition
checks, explicit clips-only order/repetition/error tests, other laptops or the
integrated Want -> Eat -> Apple -> Review -> Speak journey. Their pending status
is unchanged. Issue #5 remains OPEN/In Progress and draft PR #15 stays unmerged
pending the user's approval. Independent read-only review of this documentation-
only evidence update: **PASS**, `/root/asset_rereview`, October 10, 2026,
02:42 UTC+08; no findings. The reviewer checked the diff and prospective PR body
for truthful attribution and scope. Workspace quick verification and diff checks
PASS. No code/assets changed, so product verification was not repeated for this
evidence update; previous code verification remains recorded separately above.

A local review ZIP and patch are prepared at `reports/tanaw-04-review.zip` and
`reports/tanaw-04-review.patch` (ignored generated artifacts). The ZIP contains exactly
the seven scoped source/evidence files, no Git metadata or identity/credentials.
The package was prepared before this review-status update. No automated sending
was performed; it remains a snapshot of the submitted code and original evidence.

## PR #15 human asset acceptance follow-up — October 10, 2026

The user requested Earl's personal audit and then clarified that Earl and Gab
are the same person; use **Gab**. The supplied QA JSON names listener Gab,
witness Robin, laptop LOQ, Windows 11 and Chrome 154 user agent. No GitHub
reviewer identity is inferred from the witness name. Each of the 32 WAV labels
and 32 pictures is explicitly marked PASS with an individual check time, context
and asset hash; no unclear asset or FAIL was reported. Exact asset-check interval:
03:14:11.894–03:17:07.532 UTC+08. Source UTC timestamps are preserved.

[The normalized evidence excerpt](evidence/2026-10-10-loq-assets.json) retains all
individual asset results; it is clearly identified as an excerpt, not the full
raw helper-event stream. [The acceptance matrix](asset-acceptance.md) records
every canonical ID independently. The provenance manifest now supports actual
PENDING/PASS/FAIL plus required tester/witness/device/time/source/hash evidence.
The 64 asset byte hashes, canonical vocabulary, helper and GPL license are
unchanged. Changed bytes require new human audits; old PASS cannot carry over.

Zira's exact reported name/URI is `Microsoft Zira - English (United States)`,
language en-US, localService true. The reported base Git revision is `7c9e886`
with uncommitted QA form changes; the raw asset bytes match that reviewed base.
The browser's connectedHint was true at page load and the human physical-
disconnection attestation was true. A browser hint neither certifies nor refutes
physical disconnection; explicit Wi-Fi/Ethernet details are requested for fallback.

In the original asset JSON, all **seven supplied human fallback rows are PENDING**. The completed repeated-card
helper event used verified Zira with zero audited clips at that time; it does not
establish bundled fallback. Stop/replacement events and expected unavailable/
invalid-input errors are retained as observations, not converted to human PASS.
Current QA now captures effective request mode so unavailable-mode events do not
mislabel a stale voice preference as the voice used for that operation.

QA offers separate per-card PASS/FAIL notes, human/device context, downloadable
evidence, explicit missing-media 404 and same-tester/device audit restoration
after reload. Restore retains original witness/check times, never imports voice
verification and cannot approve another laptop. Promoted QA regression tests cover
late/local-only Zira, missing identity/FAIL notes, image failures and stale callbacks,
clip readiness, missing media, physical-disconnection gates, audit restore and
effective mode logging. At commit 3fd47c0, frontend count: **46** (31 speech, six assets/human
records, six QA regressions, three foundation). Historical 18/34/37 counts above
describe prior commits. Canonical verification for 3fd47c0
passed, including seven backend tests, build, dependency compatibility, loopback
smoke, harness checks (one skip) and secret scan. Independent read-only re-review
by `/root/asset_rereview`: **PASS**, October 10, 2026, 03:31 UTC+08, no findings.
The reviewer independently repeated canonical verification and checked all 64
asset bytes against the reviewed base, HTTP delivery and human evidence. This
approves the changed QA/code/evidence checkpoint; bundled fallback was PENDING at that review.

**Subsequent fallback report, October 10, 2026, recorded 03:39:57 UTC+08:**
after instructions for the Human offline fallback controls, Gab replied
"it is all pass". Record ordered cards, repetition, Stop, Replay, disconnected
reload and missing-media handling as **PASS (general human self-report)** on this
laptop. [The follow-up record](evidence/2026-10-10-loq-fallback-self-report.json)
retains the exact statement without inventing individual check times, Stop delay,
request modes or current witness presence. The combined browser/server restart
had explicitly been deferred. A subsequent supplied JSON reports all seven rows
PASS, including restart, but every row has null check time/context. Gab confirmed
"i changed it to pass because i tested it and it is pass but i cant change it".
Record all seven as manually entered human PASS, with validated detail pending.
The supplied global session repeats 7c9e886/Gab/Robin/LOQ/Windows 11, and its events
retain the earlier Zira/candidate-WAV times; no new bundled sequence, missing-media
event or specific browser/server restart detail is present. Explicit Wi-Fi/Ethernet
details and a fresh valid export are requested. The original asset JSON is
preserved unchanged. The additional
clips-only full-text rejection check remains PENDING.

The QA page now explains each rejected fallback result beside its control: missing
identity fields, absent physical-disconnection attestation, incomplete audio audits
or text-voice mode. It gives the next action and retains the evidence gates; no
status is automatically passed and no null time/context is filled retrospectively.
A regression covers these failures and successful manual marking in clips-only
mode. Current count is **47** frontend tests (31 controller, six assets, seven QA,
three foundation). Canonical verification passed for this fix: all 47 frontend
and seven backend tests, build, dependency compatibility, loopback smoke, harness
checks (one skip) and secret scan. Independent read-only re-review by
`/root/asset_rereview`: **PASS**, October 10, 2026, 03:46 UTC+08, no findings.
The reviewer independently reran all 47 frontend tests and checked parsing,
diffs, live module delivery and the distinction between manual PASS reports and
validated fallback evidence. This checkpoint remains subject to human merge review.

Other three laptops and final integrated React AAC/Ollama-stopped checks remain
PENDING. Issue #5 stays OPEN; PR #15 remains the existing draft. Codex must not merge.

Current remaining dependencies: human audible-label and picture-recognition audits
of any changed assets; complete bundled-fallback and disconnected checks
on all laptops; RobinKielll's integration after design approval; and final fresh
setup/demo evidence on the integrated build. Canonical vocabulary and asset paths
are available from the merged Issue #1 foundation. Suggestions remain disabled
behind their separate gate.
Feature freeze October 10 06:00, demo-ready 08:00 Philippine time (UTC+08).

Web API implementation reference: [MDN localService](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService)
and [Web Speech specification](https://webaudio.github.io/web-speech-api/#tts-section).
