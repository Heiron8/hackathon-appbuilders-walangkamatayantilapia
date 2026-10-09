# Exact-export redistribution review

**Status: NOT CLEARED. Redistribution is a blocking PR #17 requirement.**

Scope is every one of the 43 SVG files listed in `source-manifest.json`, including
all board, essential-response, preview, identity, speaker and selected-check
exports. That manifest binds each exact filename to its SHA-256 and original
dimensions; `approved-board.test.mjs` independently verifies the current bytes.
No SVG bytes were changed by the blocker fixes.

Source inspected October 10, 2026: Figma file
`SBBf5c8ejKjxcW70Fyw29N`, exported tablet frame `31:10`, native picture components
on page `26:12`. MCP's read-only component inspection finds local editable
components, with descriptions saying recognition and redistribution rights are
pending. Local/native geometry and a Figma export URL do not establish authorship
or permission to redistribute.

Recovered design-session scripts contain explicit locally written vector paths
for earlier monochrome placeholders. Those differ from the current colored
exports and do not prove the origin of every current SVG. The Want reaching
replacement has an explicit SVG creation record. None of these records is a
human authorship declaration or distribution grant covering the full exact
43-export set. No third-party license or complete source-author record for that
set has been found.

RobinKielll has been asked to identify the exact artwork author(s), any
third-party sources, and permission to distribute these exports with Tanaw, or
provide approved alternatives with compatible rights and required attribution.
Until that actual evidence is supplied and independently checked, keep
`source-manifest.json`'s `redistribution_review` as `pending`; do not call the
artwork licensed, clinically validated or ready for redistribution.

Recognition and redistribution are separate. A rights clearance must cover the
specific hashes in this manifest. Audits/licenses for PR #15's different symbol
bytes cannot clear the current Figma exports. No project-wide license choice or
new authorship claim has been made by this audit.
