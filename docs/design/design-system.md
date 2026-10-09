# Design System

Status: core visual foundation approved by [Heiron8](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087693386); [independent Design QA PASS](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087806342), October 10, 2026. Source: existing [Figma components and tokens](https://www.figma.com/design/SBBf5c8ejKjxcW70Fyw29N?node-id=26-12). No new visual direction is introduced by frontend translation.

## Tokens

| Purpose | Approved value |
| --- | --- |
| Canvas / surface / companion | `#fbf8f2` / `#ffffff` / `#f2f5f0` |
| Ink / secondary text | `#25352f` / `#56665f` |
| Primary speech / selected boundary | `#135d60` |
| Peach / mint / blue / warm | `#fbe6d8` / `#e1f1e8` / `#e4f0fa` / `#fff0db` |
| Ordinary boundary / disabled surface | `#6d8074` / `#e7ebe7` |
| Spacing | 4, 8, 12, 16, 24 px; preserve the 8 px rhythm |
| Card / control radius | 20 / 16 px |
| Surface shadow | 0 3px 12px, `#2138300f` |

Figma uses Inter; the approved web brief permits local system typography. Preserve hierarchy: card labels 22 px tablet/desktop, 20 px phone; headers 24/28 px; body 18/24 px; utilities/status at least 16/22 px. Do not fetch cloud fonts.

## Reusable controls and assets

Use native labeled buttons composed into Communication Card, Essential Response, Message Preview, editable Message Token, Action, Status and Companion Panel. Board pictures occupy 64 px slots; tablet previews 48 px; compact phone previews 32 px. Keep exact approved native pictogram exports and readable labels together. Do not redraw symbols, use emoji substitutes or bundle a Figma screen screenshot. Source artwork is replaceable and must not be described as clinically validated or licensed without evidence.

Default phone previews use 110x64 px for short labels and 160x64 px for Something else, Finished, Repeat, Banana, School, Outside, Parent and Teacher. Something else uses two lines. Wrap ordered previews; allow vertical review without truncating selected meaning. The intentional editor provides full-size tokens and 48 px Remove / Move earlier / Move later controls.

## Accessibility and states

Communication cards are at least 114x136 px in the reviewed frames, essential responses 64 px high, utilities/navigation at least 48 px. A meaningful check and border accompany selected color. Keyboard focus is visible; controls have semantic names such as Remove Apple. Actual keyboard, screen-reader, text zoom and physical-device behavior require rendered implementation QA. Honor reduced motion; no timed choices or automatic speech/focus changes.

Fresh sampled contrast: primary 7.60:1; disabled text 5.04:1; phone labels 11.14:1; compact previews 11.02:1; phone focus boundary 6.36:1. Preserve at least 4.5:1 text and 3:1 meaningful boundaries when translating the components.

Speak is an explicit action. Stop AAC selects a communication word; Stop audio interrupts playback. Unavailable speech is shown truthfully. AI assistance remains secondary and never gates board selection/direct AAC. Original pictures stay visible; candidate approval and speech are separate actions; any word edit invalidates approval and pending output. Conversation remains disabled for the MVP.
