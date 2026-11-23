# Round 115 — Reddit post-level spoilers cover the complete body (2026-11-13)

Scope: ordinary Reddit relay-to-Discord card rendering, focused offline regressions, and current
behavior documentation. This does not change intake parsing, the Devvit relay, post titles, rich-text
spoiler selection, or the established video-tile default.

## Evidence and behavior distinction

The supplied Reddit screenshots and the relay record demonstrate two independent spoiler controls:

1. A post-level Reddit **Spoiler** tag hides the complete post body/description and media behind the
   reveal action, including a text-only post with no media.
2. Rich-text spoiler formatting hides only the selected text. It still works when the post-level tag
   is absent and must not be promoted to a whole-post spoiler.

In the normal relay path the post-level flag already reached Discord image/GIF media items, but the
body was only hidden under the separate `SPOILER_MEDIA_AND_BODY` option. Consequently the body could
be exposed even though Reddit hid it. That mismatch—not media spoiler behavior or rich-text spoiler
formatting—is the correction here.

## Change

When the ordinary post-level `spoiler` flag is true, the card builder now wraps every non-empty
rendered body line in Discord spoiler syntax before splitting the body to fit Discord's message
budget. Any overflow therefore retains the spoiler formatting when sent as continuation pages. This
also covers text-only cards with no media. When the post-level flag is false, selective rich-text
spoilers pass through as before.

The post-level flag continues to spoiler image/GIF tiles by default. Video tiles remain unspoilered
by default because Discord's video spoiler cover may obscure player controls. The existing
`SPOILER_MEDIA_AND_BODY=1` switch remains available specifically to additionally cover video tiles;
whole-body spoiler handling is no longer gated by that custom setting. No change to title, footer,
stats, buttons, relay revision handling, media resolution, or custom feature intake.

## Regression coverage

The offline smoke suite now asserts that:

- short and text-only post-level-spoiler bodies are hidden with the optional switch off;
- a rich-text-only spoiler hides only its selected phrase when there is no post-level flag;
- long post-level-spoiler bodies remain spoiler-wrapped on the main card and continuation pages;
- image/GIF covers remain unchanged and video tiles are still covered only by the opt-in.

Run with `python tests/test_smoke.py`.
