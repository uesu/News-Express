# Round 117 — one-click reveal for complete Reddit spoiler bodies (2026-11-13)

Scope: Reddit post-level Spoiler text rendering in `testing area/reddit_main_v3.py`, focused offline
regressions, and behavior documentation. No Devvit relay, intake schema, title/metadata, or normal
rich-text spoiler behavior changes.

## Requested behavior

The supplied proposal and Discord screenshots distinguish the post-wide Spoiler tag from selective
rich-text spoiler markup. With the post-level flag, the full multi-paragraph description should be
hidden behind one Discord spoiler reveal, not many per-line/per-paragraph reveal controls. The title
and metadata remain outside the body wrapper. The existing media spoiler behavior is retained.

## Implementation

The body is split to Discord's size budget before adding post-level spoiler syntax. A body that fits
one message gets one opening and one closing `||` around the complete rendered text, including
paragraph breaks. A body that spans multiple Discord messages gets one balanced wrapper per message
chunk; a Discord spoiler pair cannot span separate messages. Existing inline gallery markers stay
outside text wrappers so they can be rendered as separate media components, whose spoiler covers
remain handled by the existing media logic. Existing rich-text `||…||` is unwrapped only when a
post-level spoiler is applied, avoiding nested spoiler delimiters.

Without the post-level flag, selected rich-text spoilers remain selective. Titles, metadata and
controls remain visible. Image/GIF post-level spoiler covers are unchanged; video covers remain an
optional `SPOILER_MEDIA_AND_BODY=1` behavior and are not required for body hiding.

## Regression coverage

`tests/test_smoke.py` verifies one pair spans multiple paragraphs, the title stays visible, short and
text-only bodies remain hidden by default, long body chunks are individually balanced, selective
rich-text spoiler behavior is preserved, and existing media spoiler behavior remains unchanged.
