# Round 54 — Embeddit rewrite readiness: Component-Embed auto-adaptation (2026-10-02)

## Why now

[The Embeddit rewrite](https://github.com/DeltAndy123/Embeddit/pull/2)
(branch `rewrite`, sources read 2026-10-02) is a complete rewrite of the
hosted instance this monitor uses as its rank-3 proxy-media service:

* Bun + Hono replace Express;
* Discord **Component Embeds** replace the Mastodon spoof;
* the rewrite's router (`src/index.ts`) exposes only `/r/*`, `/u/*`,
  `/user/*` and `/test` — **`/api/v1/statuses/<id>` no longer exists.**

The instance can migrate to it at any time. Without preparation, the day
that happens every status-API request would 404 and round 53 would drop
Embeddit for every run until this repo shipped a new parser. Round 54
removes that future outage: the monitor detects the migration **at
runtime** and keeps using the instance through its new page.

## What the rewrite serves (verified against the `rewrite` branch sources)

The same public post path this module already builds —
`/r/<sub>/comments/<id>/<title>` (also `/u/`, `/user/`) — is served to bots
(`botOnly` middleware; our Discordbot UA qualifies) as an HTML shell whose
only payload is:

```html
<script id="discord:component-embed" type="application/json">
  {"component": { <Discord Components-V2 container> }}
</script>
```

(`src/views/EmbedPage.tsx`, `src/views/JsonScript.tsx`.) The container
(`src/embed/builders/post.ts`, `parts.ts`, `components.ts`) holds everything
the Mastodon JSON held:

| Component | Content |
|---|---|
| TextDisplay (type 10) `-# in **[r/sub](…)**  •  by **[u/author](…)**` | subreddit + author |
| TextDisplay `### <title>` | title |
| MediaGallery (type 12) `items[].media.url` | image, gallery (captioned `(n/N)`, ≤ 10 items), or the video `fallback_url` |
| Section (type 9) + Thumbnail accessory (type 11) | link posts: destination line + preview image |
| TextDisplay `**<:u:…>  N   •   <:c:…>  M**` | upvotes • comments (compact numbers, custom emojis) |
| TextDisplay `-# Posted <t:…:R> …` | footer (+ crosspost note) |

JSON `<` may arrive escaped as `\u003c` (`escapeJsonForScript`) —
`json.loads` handles that natively.

## The run-scoped three-state machine (`testing area/reddit_proxy.py`)

```
mastodon (default)  — today's behavior byte-for-byte. Timeouts/429/5xx/parse
                      misses stay per-post misses, exactly as before.
       │ status API answers ROUTE-GONE evidence
       │ (404/410/501, or a 200 that is not JSON — the pre-rewrite live
       │  instance answers an unknown/dead POST with Cloudflare 502,
       │  verified 2026-10-01, never 404)
       ▼
   probe the Component-Embed page with the SAME post
       │ parses                         │ does not parse
       ▼                                ▼
component                          unavailable (round 53)
  one WARNING, then every            one WARNING, embeddit dropped from
  later embeddit lookup this         the dispatch order for the rest of
  run goes straight to the           the run (never below one service)
  bot page; embeddit STAYS in
  the dispatch order
```

Every monitor run is a new process, so each run starts back at `mastodon`
and re-verifies the instance — zero extra requests in the common case
(healthy instance: one request, same as today; migrated instance: one extra
page fetch on the first post only, then one request per post).

New pure parser: `parse_embeddit_component_page()` → the **same normalized
dict** every other service parser emits (`service/title/author/subreddit/
body/stats/media`), so the round-49/50 dispatch, tie-breaks, grace windows
and card pipeline need **zero changes**. Unknown component types are
skipped (forward-compatible). A body line that merely contains `•` cannot
be eaten as the stats line (the whole emoji-stripped line must match).

## What deliberately did NOT change

* Embeddit's field-table caveats stay true in the rewrite: the video is the
  DASH `fallback_url` (**no audio**) and galleries cap at **10 items**
  (`MAX_GALLERY_ITEMS`) — so embeddit remains the last-resort service and
  the round-49 tie-break order is untouched.
* `fetch_embeddit_stats` (the stats backfill) transparently benefits: it
  calls the same `_fetch_embeddit`, which serves stats from either mode.
* The warm-up, health file, share-link handling, wave dispatch and
  `proxy_services_for` rules are unchanged (component mode keeps embeddit
  in the order; unavailable drops it, round 53).

## Regression coverage (offline, no network)

`tests/test_smoke.py` round 54 block — fixtures mirror the rewrite's
builders byte-for-byte:

* gallery page → normalized shape (title/author/subreddit/body), compact
  stats through the custom-emoji markup, media kinds image/gif/image;
* video post → `kind=video` from the DASH fallback URL;
* link post → section text kept as body + preview thumbnail as media;
* a body line containing `•` is NOT mistaken for stats;
* `\u003c`-escaped JSON parses; a page without the script parses to None;
* mode machine (fake aiohttp session): route-gone + parseable page →
  auto-switch, embeddit stays in the dispatch order, later lookups cost
  exactly one page request; route-gone + unusable page → round-53 drop with
  the reason preserved; a healthy Mastodon answer keeps today's
  single-request path with no mode change; a transient 502 stays a
  per-post miss.

## Operator notes

* **No action needed before, during, or after the instance migrates
  to the rewrite.** The switch is automatic, per-run, and logged with one WARNING
  line (`embeddit: … switched to the component parser …`).
* If the instance's live format ever differs from the one read on
  2026-10-02, the probe simply fails to parse and the round-53 behavior
  (drop for the run, vxreddit/redditez/native unaffected) applies — the
  monitor can never do worse than it does today. Update
  `parse_embeddit_component_page` to the live format then.
