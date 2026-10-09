# Tanaw Shared Data and API Contracts

Status: APPROVED as part of Tanaw MVP v0.1 architecture on October 9, 2026, subject to the kickoff conditions. Examples specify future behavior; no API or shared data file has been implemented. Shared-file changes are owned by Developer 1 and require coordinated review.

## Vocabulary v1

One canonical `shared/vocabulary.json`, statically bundled into the frontend and loaded by the backend. Root: `{ "version": "tanaw-v1", "cards": [...] }`. Card: `{ "id": "apple", "label": "Apple", "category": "food", "symbol_path": "symbols/apple.svg", "audio_path": "audio/en/apple.wav", "order": 19 }`. Paths are local relative assets under the frontend public assets directory; no remote images/fonts/audio. Optional translations are future explicit additions. Planned English baseline; offline speech remains unverified.

Approved initial seed, grouped for readability. Flatten this exact sequence to derive zero-based `order`; do not alphabetize or reorder dynamically. Categories are labels, not filters that hide cards during question suggestions.

| Category | IDs and labels in fixed order |
| --- | --- |
| Essential | `no` No; `stop` Stop; `help` Help; `repeat` Repeat; `something_else` Something else; `yes` Yes |
| Core | `i` I; `want` Want; `not` Not; `more` More; `finished` Finished |
| Actions | `eat` Eat; `drink` Drink; `play` Play; `go` Go; `rest` Rest |
| Drinks | `water` Water; `milk` Milk; `juice` Juice |
| Food | `apple` Apple; `banana` Banana; `rice` Rice; `bread` Bread |
| Activities | `toy` Toy; `ball` Ball; `music` Music |
| Places | `home` Home; `school` School; `outside` Outside; `toilet` Toilet |
| People | `parent` Parent; `teacher` Teacher |

IDs are unique immutable strings. Repeated selections are allowed and retained. Message order is the selection order, never the board order. Selection limit: 12 cards; reject additional selections with a visible explanation. Baseline text joins labels in order; display the original symbols/labels at all times. Empty message cannot Speak or expand.

The frontend bundles its own vocabulary snapshot for baseline use; do not gate board rendering on an API fetch. Inference requires a matching backend vocabulary version. Unknown/stale vocabulary disables inference, not the board.

## Shared UI state and speech boundary

Frontend state: `selected_card_ids`, monotonic `revision`, `candidate`, `approved_text`, `request_id`, and playback state. Selecting/removing/clearing a card increments revision, discards candidate/approval, and invalidates pending responses. Navigation preserves selection. Explicitly clearing requires confirmation; Undo removes the latest selection without drag gestures.

Candidate approval is a separate action from Speak. Explicit editing invalidates AI approval; a deliberate Use edited text action establishes the user's chosen text, followed by Speak. Manual edits are authored by the user, not asserted to be validated AI output. Speaking never happens automatically after selection, inference, approval, or editing.

Developer 4 provides frontend functions `speakText(text)`, `speakCards(cardIds)`, and `stopSpeech()`; expose capability `full_text | cards_only | unavailable` and playback/error state. `speakText` uses only a tested local voice. `speakCards` may use that voice or play bundled clips in order. Only one playback runs; starting a new explicit playback stops the previous one. A failed text attempt does not silently substitute different card speech. Missing local voice presents a separate Speak selected cards choice. Browser speech stays usable when backend/Ollama stops.

## Common request/response rules

JSON only; reject unknown fields. Request body maximum 16 KiB. `request_id`: caller-generated UUID; `revision`: nonnegative integer; `vocabulary_version`: exact `tanaw-v1`. Selection IDs: 1-12 known IDs; preserve duplicates/order. Locale: `en` only until additional language gates pass. Backend response IDs/revision must echo the request; frontend additionally compares its current selection or question snapshot before applying results.

Error envelope: `{ "request_id": "<uuid-or-null>", "error": { "code": "ai_unavailable", "message": "Sentence assistance is unavailable. You can still speak selected cards." } }`. Never include stack traces, raw prompts, model reasoning, or model output in errors.

| Outcome | HTTP / code | UI behavior |
| --- | --- | --- |
| Schema/unknown ID/locale invalid | 422 / `invalid_request` | Retain message; explain invalid request |
| Vocabulary mismatch | 409 / `vocabulary_mismatch` | Disable inference; retain bundled board |
| Oversized body | 413 / `request_too_large` | Retain message; explain input limit |
| Model unavailable/not pulled | 503 / `ai_unavailable` | Retain message; direct speech works |
| Suggestions disabled | 503 / `feature_disabled` | Hide/disable suggestion action; ordinary board works |
| One inference already active | 429 / `ai_busy` | Retain message; no queued automatic retry |
| Five-second total deadline | 504 / `ai_timeout` | Retain message; direct speech works |
| Invalid/invented model output | 502 / `invalid_ai_output` | Discard candidate; direct speech works |

All application paths, including validation errors, use this envelope; Lead/Backend owner implement the appropriate FastAPI error handlers. Invalid requests may have null request ID. Frontend can stop waiting after six seconds and discard late results without relying on model cancellation.

## GET /api/health

Bounded readiness check, no model inference/download. HTTP 200 when backend itself is ready, even with AI down. Example:

```json
{"status":"ok","vocabulary_version":"tanaw-v1","ai":{"state":"ready","suggestions_enabled":false}}
```

AI state: `ready | unavailable | warming | unknown`. `ready` means runtime reachable and configured model present; only a successful inference demonstrates usable performance. Speech capability is browser-owned and absent from backend health. Baseline does not wait for this endpoint.

## POST /api/expand

```json
{"request_id":"11111111-1111-4111-8111-111111111111","revision":3,"vocabulary_version":"tanaw-v1","locale":"en","selected_card_ids":["want","eat","apple"]}
```

Accepted model-generated candidate:

```json
{"request_id":"11111111-1111-4111-8111-111111111111","revision":3,"vocabulary_version":"tanaw-v1","status":"candidate","source_card_ids":["want","eat","apple"],"text":"I want to eat an apple."}
```

Unsupported selection is HTTP 200 with `status: "unsupported"`, same IDs/revision/version, `source_card_ids` unchanged, and `text: null`. No claim that an expansion was generated; the original message remains usable.

P0 accepted grammar is deliberately finite:

- Optional initial `i`, optional `not`, then `want` and a single approved object noun (`[i?, not?, want, object]`): `I want <object>.` / `I do not want <object>.`
- Optional initial `i`, optional `not` immediately before `want`, then `want`, `eat`, and one food ID: `I want to eat <food>.` / `I do not want to eat <food>.`
- Same shape with `drink` and one drink ID: `I want to drink <drink>.` / `I do not want to drink <drink>.`
- Positive forms may use `I would like ...` instead of `I want ...`; negation uses only the specified negative form. Articles: `an apple`, `a banana`, `a toy`, `a ball`; other approved nouns are uncountable/no article. Approved object nouns: the food, drink, and toy/ball IDs above.

First-person phrasing for an omitted `i` is the approved explicit grammar convention for user-selected Want; its model behavior must still pass evaluation. Every content concept and negation comes from selected IDs. Do not turn `water` into `I am thirsty`, `eat apple` into `I want to eat an apple`, or `no` into a positive answer. All other shapes, ambiguous uses of No/Not, repeated-content sequences, places/actions outside these patterns, or model outputs outside exact permitted renderings return unsupported/invalid output.

Backend derives permitted renderings from selected IDs, asks Ollama for `{ "source_card_ids": [...], "text": "..." }` using JSON schema, then checks exact source sequence and permitted text (allow only whitespace/case/final punctuation normalization). Reject extra content, pronouns outside the approved convention, quantities, feelings, new preferences, dropped negation, and reordered source IDs. Do not return raw model text on rejection. No second LLM validator, confidence score, or user approval alone substitutes for these deterministic checks. Actual accepted model output is shown; deterministic direct AAC is visibly separate.

## POST /api/suggest (conditional)

```json
{"request_id":"22222222-2222-4222-8222-222222222222","revision":5,"vocabulary_version":"tanaw-v1","locale":"en","question":"What would you like to drink?"}
```

```json
{"request_id":"22222222-2222-4222-8222-222222222222","revision":5,"vocabulary_version":"tanaw-v1","card_ids":["water","milk","juice"]}
```

Question: 1-240 trimmed characters. Model returns zero to six unique vocabulary IDs, no generated answers/free text or confidence claims. Backend validates whitelist, count, uniqueness, and version. Empty IDs means no relevant options; never force a guess. A result is a neutral set of communication options, not the child's inferred intent. Essential controls remain in the primary board/essential strip even when not returned. Maintain full vocabulary access; do not reorder the primary board or auto-append a suggested card.

Question editing increments revision and invalidates pending options. The AI request omits conversation history/identity. Untrusted question content cannot alter the allowed schema/runtime or select an answer. Keep this endpoint/feature disabled until the independent relevance/safety/offline gate in the architecture overview passes.
