# Tanaw: Figma AI Handoff Brief

Status: UX BRIEF / VISUAL DIRECTION APPROVED in the Tanaw MVP v0.1 kickoff; EDITABLE DESIGN REVIEW PENDING. Ready to paste into Figma AI; no Figma file has been created. Editable design requires human review before frontend implementation. Architecture/brief approval does not imply final design approval. Developer 2 owns Figma preparation; Developer 4 supports QA and the Lead/human reviews it. Human reviewer/name/date: pending.

## Purpose and users

Create an editable design foundation for **Tanaw**, an offline picture-to-speech AAC web app. Primary users are non-speaking/minimally speaking children, including users with motor, attention, or literacy support needs. Parents, teachers, and caregivers assist with typed questions and setup. The child controls the message; AI offers optional wording/options, never a response decision. Do not make clinical efficacy claims.

Platform: local browser on a laptop, with responsive tablet/mobile layouts. Apple/iPadOS-inspired visual restraint, not a native iOS app. Do not require Apple fonts, cloud assets, account screens, or paid design libraries.

## Exactly three primary screens

Design these as three views of one shared communication shell, not separate products. Preserve the vocabulary grid's position and order within each viewport. Use a reserved companion panel (side panel on laptop/tablet landscape; fixed region above the grid on narrow layouts), so switching between views does not insert content into/reorder the board. Message strip and essential responses remain available. Longer panel content scrolls inside the reserved region; do not push the grid downward after an AI result arrives.

| Screen | Required content | Required states |
| --- | --- | --- |
| 1. Communicate | Labeled picture grid, ordered message strip, Speak selected words, Undo, Clear, Improve sentence; simple connection/speech status | Empty; composing; selection limit; speaking/stopped; AI unavailable; local full-text voice unavailable with card-audio option; all speech unavailable |
| 2. Review Message | Original cards/words next to suggested sentence; Use this sentence; edit field; Use edited text; Speak approved sentence; Keep original / return | Loading; candidate awaiting approval; approved; editing/unconfirmed; unsupported; invalid result; timeout; stale candidate discarded; full-text speech unavailable |
| 3. Conversation | Caregiver-labeled typed-question field, Get options, zero-to-six existing picture-card options in companion panel; same complete board/message | Feature disabled; empty question; loading; options ready; no relevant options; error/timeout; question edited/stale results; selected option appended |

Review Message is an explicit companion-panel mode of the board: avoid a blocking modal that hides essential communication. Conversation remains conditional: show its disabled design state but do not claim it works before feasibility approval. No fourth screen/onboarding/settings dashboard is required; a small caregiver speech-choice popover belongs to the shared shell.

## Exact journeys

1. **Direct communication:** open Communicate -> select Want, Eat, Apple in that order -> message strip shows those cards/words -> Speak selected words -> offline output speaks the selected wording -> selections remain for correction/replay.
2. **Assisted wording:** select cards -> Improve sentence -> Review Message shows original plus pending state -> candidate appears -> Use this sentence -> Speak approved sentence. Keep original returns to direct wording. Editing requires Use edited text before speaking; card changes invalidate approval/candidate. Never auto-speak after approval.
3. **Question assistance (conditional):** caregiver opens Conversation -> types "What would you like to drink?" -> Get options -> Water/Milk/Juice may appear -> child may select one, use any full-board card, or choose No/Stop/Help/Repeat/Something else -> message strip updates -> ordinary explicit Speak/review path. Suggested options never become the child's answer automatically.
4. **AI failure:** model unavailable/timeout/invalid output -> brief status "Sentence assistance is unavailable. You can still speak selected cards." -> original message, board, and direct speech remain functional.
5. **Speech fallback:** full-text local voice unavailable -> show "Full sentence voice is unavailable" and explicit Speak selected cards when bundled clips work. If neither speech path works, show a truthful speech error; do not show successful playback.

## Communication cards and shared message rules

Use the complete 32-card vocabulary/order from [contracts.md](../architecture/contracts.md). The first six IDs are No, Stop, Help, Repeat, Something else, Yes. Make the first five essential responses always accessible in a consistent strip; their full-board instances keep canonical positions. All instances reference the same IDs, not duplicate vocabulary records. Complete vocabulary is never restricted by suggestions.

Each card has a recognizable locally bundled symbol plus a persistent plain-language label. Category color is optional and secondary. Selected styling uses a border/check/state, not color alone. Tapping appends one card; repeated taps intentionally append repeats. Do not toggle/delete a card by tapping its grid instance. Undo removes the last selection; message-strip Remove controls allow explicit correction without drag gestures. Clear asks for confirmation. Maximum 12 selected cards; explain the limit without losing the message.

Use keyboard-operable native-button behavior and predictable row order. No drag-only actions, timed choices, hover-only information, automatic movement, or auto-speech. Distinguish the Stop communication card from Stop audio; distinguish the Repeat communication card from Replay audio. Navigation retains selections; reloading starts a new empty session. Show original wording throughout AI review. Only explicitly approved/user-confirmed text can be spoken as the revised sentence.

## Visual direction

Friendly, quiet, spacious Apple/iPadOS-inspired web interface: warm off-white background, dark slate text, restrained soft teal/blue accents, generous spacing, clear typographic hierarchy, and consistent 16-20px rounded cards. Prefer flat grouped regions and subtle separators. Keep the board visually dominant and actions easy to find.

Use locally available `system-ui` typography; plan 20-24px card labels on laptop/tablet, never shrink essential labels merely to fit. Message strip text around 24px; utility labels at least 16px. Use an 8px spacing rhythm. Prototype colors must be contrast-checked; pastel text on pastel cards is unacceptable. Motion is brief/purposeful, respects reduced-motion, and never rearranges cards.

Create reusable editable Figma components: Communication Card (default/focus/selected), Essential Response, Message Token with Remove, primary/secondary action, typed-question field, suggestion option, status message, and companion panel. Show empty/loading/error/approval states as variants. Avoid flattened screenshots as the design handoff.

## Accessibility and responsive constraints

- Proposed communication targets >=64x64px, utility targets >=48x48px with clear separation. Visible keyboard focus, logical tab order, meaningful accessible names, and state announcements that do not interrupt every card action.
- Text contrast >=4.5:1; meaningful focus/control boundaries >=3:1. Symbols plus labels; no color-only meaning. Clear pressed/selected state, error copy, and enabled/disabled distinction.
- Keep Speak, Undo, and essential responses discoverable. Only inference controls are disabled while AI is busy; direct speech/selection stay available. No timed dismissal or automatic focus jumps when results arrive.
- Produce laptop (1440x900), tablet landscape (1024x768), and phone (390x844) variants of the same three screen families. Proposed grid: 6/4/3 columns respectively, preserving canonical row order. Reflow at viewport changes is deterministic; a suggestion/status update never changes card positions. Scrolling is acceptable; horizontal clipping is not.
- Support browser zoom/text growth and long labels without truncating meaning or hiding controls. Avoid custom text-size/theme settings in P0; implement resilient sizing and reduced motion first.
- Symbols/recordings must have verified redistribution rights. Use replaceable local placeholders in Figma until licensed assets are selected; do not invent a native-symbol-library dependency. Planned English baseline; offline speech remains unverified. Filipino wording/voices need separate checks before claims.

## Human review / implementation handoff

Reviewer checks the three journeys, user control, original/candidate distinction, essential access, stable layout, label recognition, target sizes, keyboard focus, contrast, responsive states, and truthful AI/speech failure. Record reviewer, date, Figma link/node references, and requested corrections here after review. Until then: DESIGN REVIEW PENDING; frontend implementation is not released. Detailed approved component specs/wireframes can be added to existing `design-system.md` and `wireframes.md` after Figma review; do not create competing design documentation.
