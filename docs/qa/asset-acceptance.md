# PR #15 - human asset and offline fallback acceptance

Auditor reported as Gab; witness reported as Robin. User clarified Earl and Gab are the same person and requested the name Gab.
The supplied individual human records report 32/32 audio PASS and 32/32 picture PASS. Offline fallback rows remain PENDING; prior Zira sentence/Stop/Replay/restart PASS is separate from bundled-fallback acceptance.

Use http://127.0.0.1:8770. Gab must personally listen and inspect; no generated file, unit test or browser event establishes recognition or audibility.

1. Reload the updated QA page. Enter actual tester, witness (self-witnessed if alone), laptop, Windows build and Git revision. Note uncommitted QA changes if testing before the reviewed commit.
2. Physically disable Wi-Fi, unplug Ethernet and disable other internet connections. Check the physical-disconnection attestation only after doing this.
3. Play each of the 32 WAVs. Select Audio PASS only for an understandable exact canonical label; use FAIL with the words heard and proposed correction.
4. Inspect each of the 32 pictures. Select Picture PASS only for recognizable correct meaning; use FAIL with the ambiguity and proposed correction. A load error is not recognition PASS.
5. When all audio results PASS, click Use audited clips only. Test ordered/repeated cards, Stop and Replay. Full-text Speak in this mode must report full_text_unavailable without substituting clips.
6. Click Test missing bundled Apple recording. This explicit QA fault requests /audio/en/__qa_missing_apple.wav (real HTTP 404), without deleting assets. Expect playback_failed, no sound or false success. Record the exact result.
7. Record each fallback outcome below in the page and download Evidence JSON before reload. While still disconnected, reload and then restart browser/server; enter the same Gab/Robin/LOQ/Windows 11 details and explicitly Restore recorded asset audits for this tester/device; then select clips-only and retest ordered playback. Restore retains original audit times and never restores voice verification. Save post-restart evidence separately.
8. Paste the Evidence JSON/results back. Include each failure, browser/helper errors, approximate Stop delay, witness and exact date/time. Preserve source/license notices; report defects before replacing assets.

## Individual assets

| ID | Canonical label | WAV | Picture | Human notes / evidence |
| --- | --- | --- | --- | --- |
| no | No | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| stop | Stop | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| help | Help | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| repeat | Repeat | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| something_else | Something else | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| yes | Yes | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| i | I | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| want | Want | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| not | Not | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| more | More | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| finished | Finished | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| eat | Eat | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| drink | Drink | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| play | Play | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| go | Go | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| rest | Rest | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| water | Water | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| milk | Milk | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| juice | Juice | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| apple | Apple | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| banana | Banana | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| rice | Rice | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| bread | Bread | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| toy | Toy | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| ball | Ball | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| music | Music | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| home | Home | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| school | School | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| outside | Outside | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| toilet | Toilet | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| parent | Parent | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |
| teacher | Teacher | PASS | PASS | Gab / Robin; exact times and file hashes in [evidence](evidence/2026-10-10-loq-assets.json) |

## Offline fallback

| Check | Result | Exact outcome / witness evidence |
| --- | --- | --- |
| Want -> Eat -> Apple order | PENDING | Not supplied |
| Apple -> Want -> Apple repetition | PENDING | Not supplied |
| Stop (record delay) | PENDING | Not supplied |
| Replay from beginning | PENDING | Not supplied |
| Disconnected reload + clips-only speech | PENDING | Not supplied |
| Disconnected browser/server restart + clips-only speech | PENDING | Not supplied |
| Missing-media HTTP 404 -> playback_failed, no sound/false success | PENDING | Not supplied |
| Clips-only full text -> full_text_unavailable, no card substitution | PENDING | Not supplied |

## Device and witness

Tester / actual listener: Gab (user-confirmed Earl alias; no separate tester invented)
Witness: Robin, as supplied in the human record; no GitHub reviewer identity is inferred.
Laptop / Windows / browser version: LOQ / Windows 11 / Chrome 154 user agent; exact Windows build and full browser version are not supplied in this record.
Asset checks: October 10, 2026, 03:14:11.894?03:17:07.532 UTC+08; original UTC timestamps retained in JSON.
Reported base commit: 7c9e886fc858e01e7a848beba1dd5dec49e8f312, plus uncommitted QA form changes. Actual 64 asset bytes match the unchanged reviewed assets.
Physical disconnection: human-attested true; browser connectedHint was true at page load and is not connection proof. Explicit Wi-Fi/Ethernet follow-up remains pending.
Evidence: [normalized user-supplied asset record](evidence/2026-10-10-loq-assets.json). This excerpt retains all individual asset results and exact times/context; it is not claimed to be the complete raw helper-event stream.

Prepared: 32/32 WAVs and 32/32 SVGs. Human reported PASS: 32/32 WAVs, 32/32 pictures. No asset FAIL or ambiguous picture was reported. No asset byte replacement was required.
Other three laptops and final integrated React AAC/Ollama-stopped journey remain PENDING. Issue #5 stays OPEN. PR #15 must not be merged by Codex.
