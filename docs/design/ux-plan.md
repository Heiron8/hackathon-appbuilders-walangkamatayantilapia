# Tanaw: Figma AI Handoff Brief

Status: EDITABLE CORE DESIGN APPROVED by Heiron8 on October 10, 2026 at 03:21:10 Philippine time, conditional on independent Design QA. [Actual approval](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087693386) and [fresh independent Codex Design QA PASS](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087806342) satisfy that gate. The [existing editable Figma foundation](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=26-10) is the visual reference; it was refined through MCP, not recreated. RobinKielll owns the small Issue #3 frontend checkpoint. This approval does not certify runtime accessibility, symbol recognition/licensing, AI or offline speech.

## Purpose and users

Create an editable design foundation for **Tanaw**, an offline picture-to-speech AAC web app. Primary users are non-speaking/minimally speaking children, including users with motor, attention, or literacy support needs. Parents, teachers, and caregivers assist with typed questions and setup. The child controls the message; AI offers optional wording/options, never a response decision. Do not make clinical efficacy claims.

Platform: local browser on a laptop, with responsive tablet/mobile layouts. Apple/iPadOS-inspired visual restraint, not a native iOS app. Do not require Apple fonts, cloud assets, account screens, or paid design libraries.

## Exactly three primary screens

Design these as three views of one shared communication shell. Preserve the vocabulary grid's position and order within each viewport. The approved final refinement supersedes the initial narrow-layout proposal: tablet/desktop use a reserved side panel; phone places the board before optional assistance in the scrolling workspace. Message composer, Speak and essential responses remain available outside that workspace. Review deliberately scrolls to the optional panel; Pictures returns to the board. AI results never insert or rearrange board cards.

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

Each card has a locally bundled replaceable symbol plus a persistent plain-language label; clinical recognition and redistribution rights are separate checks. Category color is secondary. Selected styling uses a border/check, not color alone. Tapping appends one card; repeated taps intentionally append repeats. Do not toggle/delete by tapping the board. The default composer shows ordered picture previews, Undo, Clear and prominent Speak. Edit words opens all selected tokens with explicit Remove and labeled Move earlier / Move later; Done returns to pictures. Longer previews and token lists scroll in order. Clear asks for confirmation. Maximum 12 selected cards; explain the limit without losing the message.

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

Heiron8's actual approval and the separate read-only Codex QA are linked above. QA freshly checked desktop/tablet/phone Communicate and Review, all 53 boards, 32 canonical IDs/order, essential access, intentional corrections, approval/invalidation, loading/error/stale/playback states, sampled contrast and disabled Conversation. No blocking design findings remain. See [design-system.md](design-system.md) and [wireframes.md](wireframes.md) for the approved handoff. Implement first the direct AAC checkpoint using the existing vocabulary and speech helper; sentence improvement follows the approved API when available. Do not infer audible/offline speech or runtime accessibility from Figma or unit tests.
