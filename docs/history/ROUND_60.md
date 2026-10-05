# Round 60 (2026-10-03) — YouTube link posts: destination-first video selection + URL unescaping

## Incident

`Zenlesszonezeroleaks__1wwgk5e` was a YouTube link post with body text. Its
actual ZZZ showcase video was the post destination:

`https://www.youtube.com/watch?v=QvhE_9XgImw`

The body also contained a `Song:` credit pointing to a different YouTube AMV.
The card, thumbnail, YouTube button, and follow-up YouTube-only message used
that first body URL instead of the showcase destination. The credit URL also
reached Discord with literal `&amp;` query separators from RSS HTML.

## Root cause

Reddit link posts now permit body text. In RSS, the destination is represented
by a trailing `<a href="…">[link]</a>` anchor **after** the body. The prior
first-match extractor therefore selected an earlier YouTube URL from the body.
It returned the raw regex match, which preserved HTML entities instead of a
usable URL.

## Decision and implementation

The V3 Reddit monitor now has a single destination-first rule:

1. `extract_outbound_url(content_html)` finds the RSS `[link]` anchor and
   returns its external destination. A text post's `[link]` points back to
   Reddit, so `reddit.com` and `redd.it` targets return `None`.
2. `select_youtube_url(outbound_url, *html_parts)` uses a valid YouTube
   destination before falling back to the existing first body match.
3. `entry_to_base_data()` applies that selector for the native RSS path.
4. FULL MODE treats `post_json["url"]` as authoritative when it is YouTube,
   so it also overrides a body-derived credit URL.
5. `extract_youtube_url()` HTML-unescapes its match before returning it.

The selected URL feeds the card button, thumbnail/video selection, and
follow-up YouTube-only message, so this single selection point corrects all
three outputs.

## Preserved behavior

- Text posts keep body-first matching because their `[link]` anchor is their
  own Reddit permalink.
- Non-YouTube link-post destinations still fall back to body matches.
- The round-38a final-body fallback remains unchanged for posts where no URL
  was found earlier.
- Already plain URLs are unchanged by HTML unescaping.

## Verification

Seven offline `r60` smoke guards replay the `1wwgk5e` RSS shape and prove:

- the trailing external `[link]` destination is extracted;
- Reddit-domain `[link]` anchors are ignored for text posts;
- the destination outranks the body `Song:` URL;
- text-post fallback remains body-first and returns a decoded query string;
- direct extraction no longer leaks `&amp;`;
- the native RSS base carries the destination; and
- FULL MODE replaces a body-derived URL with `post_json["url"]`.

No new Variables or workflow changes are required.

## Deployment

After merging this development-repository PR, copy both
`testing area/reddit_main_v3.py` and `tests/test_smoke.py` to both production
repositories. The next Reddit monitor cron tick will use the fix.
