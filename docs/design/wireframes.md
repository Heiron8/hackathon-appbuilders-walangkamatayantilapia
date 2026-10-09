# Wireframes

Status: editable core design approved by [Heiron8](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087693386), with [fresh independent Design QA PASS](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087806342), October 10, 2026.

| Layout | Communicate | Review Message | Canonical grid |
| --- | --- | --- | --- |
| Tablet 1024x768 | [31:10](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=31-10) | [31:687](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=31-687) | 4 columns |
| Desktop 1440x900 | [31:6149](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=31-6149) | [31:6784](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=31-6784) | 6 columns |
| Phone 390x844 | [31:8062](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=31-8062) | [31:8703](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=31-8703) | 3 columns |

## Shared shell

Navigation → pinned No/Stop/Help/Repeat/Something else → original ordered picture composer with Undo/Clear/Speak → canonical picture board and optional companion. Tablet/desktop place the companion beside the board. Phone uses a single 48 px navigation row and places the board before optional help; composer, Speak and essentials stay outside workspace scrolling. Review deliberately opens/scrolls to the companion, and Pictures returns to the board. Layout must grow for text zoom and shorter devices rather than clip required controls.

Every board retains all 32 IDs in canonical row-major order. Responsive column changes are deterministic; AI/speech/status changes never rearrange cards. Board geometry across reviewed state examples is stable: tablet x12,y284,664x472; desktop x24,y308,1056x568; phone x12,y428,366x404. These are reference proportions, not a requirement to hardcode browser coordinates.

## Primary journey and intentional editing

Start empty; see picture → tap → ordered selected preview → explicit Speak. Want → Eat → Apple is the first working checkpoint, not a prefilled child message. Repeated taps append duplicates; maximum 12. Undo removes the latest selection. Edit words opens a scrollable ordered token list with explicit Remove and labeled earlier/later controls; Done returns to the board. Clear requires confirmation and retains the message when canceled.

## State coverage and gates

[State examples](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=26-11) include empty/composing/repeats/limit, focus, Clear confirmation, speaking/stopped, AI unavailable, card-only speech fallback and all-speech failure. Review includes loading, unapproved/approved, edit/unconfirmed, unsupported, invalid, timeout and stale-result states; original selected pictures remain visible throughout. Phone approved example: [34:32036](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=34-32036).

Exactly three screen families exist; Conversation's future specimens do not enable the feature. Keep its navigation disabled. The first React checkpoint implements direct AAC and truthful unavailable sentence help; inference follows the approved contract when available, without fabricated candidates. Actual device speech/offline readiness, licensed assets and rendered accessibility require integration evidence beyond design QA.
