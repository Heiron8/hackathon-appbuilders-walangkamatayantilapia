---
name: demo-video
description: Prepare demo video, generate product demo, create submission video, or update demo video from real verified application footage. Use for demo-production requests; do not load for normal frontend/backend development.
---

# Demo Video

Use the [Demo Video Producer charter](../../agents/demo-video-producer/CHARTER.md), Project Sync and current human task ownership. For commands, storyboard schema, tool prerequisites and fallbacks, read [the executable pipeline guide](../../demo/README.md). Work within demo-owned files; report product defects with reproduction steps to the assigned developer. No new agent framework or submission system is involved.

## A. Inspect

Read the real product and acceptance criteria, architecture, actual source, tests and dated execution results, independent review, deployment evidence and limitations. Identify the integrated commit/build and running URL. A test file, architecture approval or workspace check alone is not product runtime evidence.

Classify candidate features: **VERIFIED** (runtime evidence for this build), **DEMONSTRABLE WITH WARNING** (real behavior with a disclosed limitation), or **NOT SAFE TO DEMONSTRATE** (unsupported, broken, private or misleading). Exclude unsafe features. Put warnings on screen and in narration when relevant. Final capture requires integrated-build verification and review references, plus a privacy check of disposable demo data. The template's new phase allows explicitly authorized generic tooling rehearsal only; challenge product architecture and implementation remain gated.

## B. Storyboard

Choose one compelling real journey. Target 60-120 seconds for a hackathon, then check actual event rules. Use problem/hook, product introduction, primary flow, strongest result/value, optional supporting feature, impact/closing. For each scene specify ID, duration, actual user actions and result assertions, narration, readable caption, evidence classification and verification references. Keep claims concise and qualified. Do not invent performance, integrations, AI capabilities or outcomes. Save storyboard JSON with the demo task's evidence.

## C. Capture

Use Playwright on the actual running application. The bundled capture driver records real navigation, input, interactions and assertions, including a relevant error/fallback path. Each scene starts in a fresh isolated context: replay its prerequisites explicitly. Use stable selectors and result assertions for readiness. The duration dwell is presentation pacing, never a substitute for readiness. Do not insert fabricated responses or edit the app DOM to simulate behavior. Before recording, inspect visible content, use sanitized test accounts/data, and ensure the human has authorized any external-state mutations needed by the flow. Keep capture free of credentials, account dashboards, private notifications and logs.

For desktop/CLI/non-browser products, use the manual recording path with the same build and evidence requirements. Keep original footage and failed-run evidence. A defect stops the affected claim/scene; report it rather than repairing product code silently.

## D. Narration

Write concise, natural English matched to each scene. Prefer installed free local speech; Windows SAPI is the tested default, with traditional synthetic voices rather than a neural AI voice. The audio adapter accepts per-scene local WAV/audio from another local TTS provider or a human. No paid API or sponsor-credit dependency. Missing local TTS is a disclosed prerequisite: use captions-only or manual narration. Keep each audio file within its scene; the pipeline fails on overlong narration rather than truncating it. Review pronunciation and synchronization in full playback.

## E. Compose

Use Remotion for actual recordings, title/closing cards, persistent captions, narration, optional highlight rectangles and simple caption fades. FFmpeg handles conversion, decoding and a simpler captioned fallback if Remotion fails; it omits optional highlights/fades. Isolate dependencies under demo/. Preserve reusable scripts and lockfile; keep generated videos, browser recordings, narration and sample app in ignored output/. Avoid advanced editing and custom infrastructure.

## F. Validate and hand off

Run the pipeline's full MP4 decode, duration, stream and narration-fit checks. Inspect exported scene frames and play the entire MP4, checking UI/caption readability, narration timing, actual footage/build identity, unsupported claims, private information and known event requirements. Obtain independent reviewer evidence; automated checks never establish these semantic claims. Report **IMPLEMENTED**, **ACTUALLY TESTED**, and **NOT YET AVAILABLE** separately, with exact tool results and output location.

Supply evidence.json, storyboard, MP4 path, build/check time and independent playback review to the existing [Submission Readiness checklist](../../docs/qa/submission-readiness.md), especially its Demo rows. Use technical-defense for a requested readiness assessment. Rehearsal evidence does not verify the challenge product; unknown event rules and missing final review remain open blockers. Creating a video does not authorize publishing/submission or bypass any phase/review gate.
