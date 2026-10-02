# Round 55 — mod-queue page evidence must render this post

## Incident

On 2026-10-02, `r/WutheringWavesLeaks/1wvlsz0` was delivered while Reddit
still showed **Post is awaiting moderator approval** and the AutoModerator
comment said it had been temporarily sent to the moderators. The hold text
patterns already matched; the failure was page evidence acquisition.

`_fetch_redlib_post_page()` accepted any HTTP 200 HTML response. A reachable
Cloudflare interstitial, JavaScript shell, or rate-limit page could therefore
be treated as the post page. With the banner sources and `/new` listing
unavailable, the shell contained no hold text and the post was released.

## Fix

`reddit_signals.page_is_post_page(page_html, post_id)` now requires the
post's own `/comments/<id>` marker. `mod_queue_reason()` filters all fetched
pages through this check before selecting queue evidence. Failed checks enter
the existing round-46b no-page branch:

* a young post with no API-backed listing proving release is held;
* an API-backed listing containing the post still releases immediately;
* after the 15-minute grace period, unavailable evidence remains bounded and
  the post is released.

The healthy-post fast path and `queue_verdict()` precedence are unchanged.

## Tests

Coverage includes real rendered pages, case-insensitive IDs, Cloudflare/JS
shells, different posts, longer ID prefixes, empty inputs, faithful round-46
page fixtures, and the existing queue decision tests.
