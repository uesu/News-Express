# Changelog archive — rounds 1–62

Full prior history of News-Express, moved out of the main README during Round 63 ("The Great Simplification") to keep the README focused on the current shipped behavior. See `README.md` for the round-63 summary and the current changelog entry.

* **2026-10-04 — Round 62: body/gallery duplicate media line scrub.**
  Live 1wx9c77 (r/Zenlesszonezeroleaks\_): a selftext whose only content is
  an inline image link rendered the SAME picture twice on the card — once
  as a raw `preview.redd.it` URL text line, once in the media gallery right
  below it. New `_drop_gallery_media_lines()` runs at card build (one
  choke point — both RSS and FULL mode, all future posts): any body line
  that is ONLY a redd.it media link (bare URL, HTML-escaped `&amp;`
  variant, or a self-labelled `[url](url)` markdown link) whose file
  identity (`_reddit_media_key`: `preview.redd.it/<slug>-v0-<id>` and
  `i.redd.it/<id>` renditions collapse to one key) already sits in the
  gallery is dropped. Prose lines, caption-labelled links, and media NOT
  in the gallery stay byte-identical; a body left empty simply omits the
  text component. 12 new smoke guards (incl. the live 1wx9c77 card shape).

* **2026-10-04 — Docs: Speed & latency guide (complete tier list).**
  Replaces the Speed presets / 5-minute combos / Cadence combos trio with
  one unified guide: the latency formula, a Variable glossary, a
  verdict-tiered table covering 15/10/5/3/2/1-minute crons
  (✅ Recommended → 🔴 Not okay, plus the ⚠️ Fastest/Instant tiers), worked
  arrival examples, and a notice with concrete trade-off scenarios.
  Research alongside: live probe of `sametcn99/reddit-rss-api` on its new
  Deno Deploy host (`reddit-rss-api.sametcn99.deno.net`) — 2/5 body-reads
  (the passes served one cached feed), the rest `UpstreamError: HTTP 429`
  (Reddit rate-limits the datacenter IP); it also reads the **hot** `/.rss`
  feed (not `/new.rss`) and emits JSON, not RSS. **Not compatible — not
  added**; consistent with the round-61 sweep: a middleman adds a hop, not
  an exemption.

* **2026-10-04 — Round 61: stale-tip double post — sync-to-tip + semantic
  cache merge.** Live 2026-10-03: a queued `workflow_dispatch` run starts
  on the tip pinned at DISPATCH time (the 2026-09-19 fix's "checks out the
  newest main" assumption is false), so run #4014 missed commit
  `2de1491`'s fresh dedup key and re-posted `1wwyure`; its cache push then
  died on a git line conflict in `pending_reddit.json`. Both monitor
  workflows gain a "Sync to the live branch tip" step after checkout, and
  the persist recovery now uses `.github/scripts/merge_monitor_caches.py`
  (semantic union merge — list union for posted keys, newest-timestamp
  wins for pending/messages, loud failure on invalid JSON) instead of
  `git pull --rebase`. Correctness is now cadence-independent (a README
  "Cadence combos" table documents 5/3/2-minute setups). 15 new smoke
  guards replay the exact incident plus an end-to-end two-clone race
  simulation. A wide feed-source sweep (RSSHub, the RSS-Bridge
  RedditBridge network, redlib RSS, hosted proxies) found **no working
  third-party Reddit feed source** — every middleman hits Reddit's
  datacenter-IP wall — so no credits were added and the fleet is
  unchanged; the native `.rss` + feed-token + Arctic Shift trio the
  engine already uses remains the only reliable class of sources.
  Details: [`docs/ROUND_61.md`](ROUND_61.md).

* **2026-10-03 — Docs: Instant preset (old-speed combo at the 5-minute cron).**
  No code change. The Speed presets table gains **Instant**: cron unchanged at
  5 minutes, `POST_SETTLE_SECONDS=0` + `POST_SETTLE_VERIFIED_SECONDS=0` +
  `MOD_QUEUE_WEAK_GRACE_SECONDS=0` + the `RETRACT_DEAD_POSTS=1` seatbelt —
  the pre-round-36 "post on first sighting" latency (cron offset only) with
  the NSFW gate and all in-run checks still armed. The ⚠️ notice now covers
  both Fastest and Instant, plus a softer variant
  (`POST_SETTLE_VERIFIED_SECONDS=0`, `POST_SETTLE_SECONDS=60`).

* **2026-10-03 — Docs: latency-tuning presets + three missing Variable rows.**
  No code change. The Variables table gains the three round-46/46b settings
  (`MOD_QUEUE_WEAK_GRACE_SECONDS`, `LISTING_TIMEOUT_SECONDS`, and
  `LISTING_HTML_GRACE_SECONDS`) that were wired into `.env.example` and the
  workflow but missing from this table. The stale “no third mod-queue Variable”
  notes are corrected, and a **Speed presets** section documents Default, Fast,
  Faster, and Fastest cron-plus-Variable combinations. Fastest requires the
  `RETRACT_DEAD_POSTS=1` seatbelt.

* **2026-10-03 — Round 60: YouTube link posts — destination-first.** Reddit
  link posts can now contain body text with multiple YouTube URLs, so
  first-match extraction selected a body credit link (`Song:`) instead of the
  post's actual video destination (live `1wwgk5e`: wrong button, thumbnail,
  and follow-up link; the showcase video was missing). The RSS `[link]`
  destination and FULL-MODE `post_json["url"]` now take priority when they
  are YouTube URLs, and extracted URLs are HTML-unescaped so literal `&amp;`
  never reaches Discord. Text posts retain their body-first behavior. Seven
  offline smoke guards replay the incident. Details:
  [`docs/ROUND_60.md`](ROUND_60.md).

* **2026-10-03 — Round 59: nitter fleet body-audit and Reddit audit record.** The three Twitter engines now share a body-audited fallback order: serving mirrors `nitter.kareem.one` and `tw.eir-nya.gay` are ahead of the token-gated host, while known challenge-wall hosts remain retained at the tail. The Reddit fallback list is unchanged after the same response-body audit found no confirmed working additions. Fork credits and the full decision record are in [`docs/ROUND_59.md`](ROUND_59.md).


* **2026-10-03 — Round 58: AGENTS.md — agent onboarding.** New root-level
  [`AGENTS.md`](../../AGENTS.md) (the emerging standard file AI coding agents
  read first) encoding the repository's operational knowledge: the
  three-repo dev/prod architecture and manual deployment flow, the file
  map, how to test, the nine never-violate invariants (NSFW gate,
  gates-never-guess, Variable wiring + empty-string safety, the P0
  concurrency rule, …), the deliberate-behavior landmine list, key
  Variable defaults, and writing conventions. Docs only — zero code or
  behavior change.

* **2026-10-03 — Round 57: workflow hardening.** Supply chain: every
  `uses:` in every workflow is now pinned to an immutable 40-hex commit SHA
  (mutable tags like `@v7` can be repointed — the 2025 `tj-actions`
  compromise, CVE-2025-30066); Dependabot keeps the pins fresh via reviewed
  PRs. Outage cap: every job now declares `timeout-minutes` (monitors 15)
  — previously a single hung network call could hold a run for GitHub's
  6-hour default and, because the P0 concurrency guard queues instead of
  cancelling, silence the monitor behind it. Zero engine/behavior change;
  smoke guards added (SHA-pin, timeout, and concurrency-guard presence).
  See [Round 57](ROUND_57.md).

* **2026-10-02 — Round 56: media heal targets videos only.** The round-47
  self-heal re-edited three photo posts whose image tiles came back from
  Discord with cold metadata, even though the photos already rendered fine
  (only the mp4 player actually needs resolved metadata — the sole broken
  tile ever confirmed was a video). `heal_eligible_items()` now limits the
  heal pass to video renditions (`.mp4/.m4v/.mov/.webm/.m3u8` or
  `video.twimg.com`, which keeps X "GIF" tweet_video mp4s covered); photos
  and converted `.gif`/`.webp` files are left alone. The Variable
  `MEDIA_HEAL_SCOPE` accepts `video` (default), `on`/`all` (restore healing
  for every media type) and `off` (disable the heal pass entirely) — no code
  change for any mode. Log wording fixed ("the media now renders").
  See [Round 56](ROUND_56.md).

* **2026-10-02 — Round 55: mod-queue page evidence must render this post.**
  A 200 Cloudflare/JavaScript shell could masquerade as a Reddit post page
  when the banner sources were unavailable, allowing a queued post to pass
  with no hold text. `page_is_post_page()` now requires the post's own
  `/comments/<id>` marker before page HTML can feed the mod-queue verdict.
  Shells route into the existing no-page branch: young posts hold unless an
  API-backed listing proves release, while healthy rendered posts retain the
  zero-latency path. See [Round 55](ROUND_55.md).

* **2026-10-02 — Embeddit incident root cause + rewrite readiness (rounds
  53–54).** The 2026-10-01 23:13 UTC production runs logged
  `embeddit error: /api/v1/statuses/…` on every post and
  `PROXY_WARMUP_POST '' is invalid … Warm-up skipped` on every run. Root
  cause: an **unset-but-wired GitHub Variable arrives as an empty string**,
  which `os.getenv(name, default)` accepts as a real value — `EMBEDDIT_BASE`
  became `""`, every Embeddit request targeted a **relative** URL, and
  aiohttp raised `InvalidUrlClientError` before opening a socket (the hosted
  instance was never at fault; the exact status id from the log returns
  valid JSON against the default host). Round 53 adds the string counterpart
  of the round-49b numeric guard (`_env_str`), normalizes
  `EMBEDDIT_INSTANCE` to an always-absolute http(s) base (bare host,
  host:port, trailing slash accepted; garbage → default + one warning),
  logs the exception class + host on embeddit errors, lets an invalid
  `PROXY_WARMUP_POST` probe the built-in default post instead of skipping
  the warm-up, and applies the same empty-means-default rule to the
  `SUBREDDITS`/`ACCOUNTS` secrets. Round 54 prepares for
  the Embeddit rewrite (Bun + Hono, Discord Component Embeds — it
  **removes** the Mastodon status API): on
  route-gone evidence (404/410/501 or a non-JSON 200 — a dead post answers
  502 on the live instance, never 404) the monitor probes the rewrite's
  `discord:component-embed` bot page with the same post and, if it parses,
  **auto-switches to the component parser for the rest of the run** (one
  WARNING line, embeddit stays in the dispatch order); if it doesn't parse,
  the round-53 drop applies — the chain can never do worse than today.
  No new secrets or Variables; no workflow changes. See
  [Round 53](ROUND_53.md) and [Round 54](ROUND_54.md).

* **2026-10-01 — Repository tracking and configuration audit.** The active
  workflow paths, legacy engines, tests, state files, runtime policy, Privacy
  Policy, Terms of Service, and historical round records were reviewed against
  the fetched `main` tree. The repository map now includes the Python bump
  workflow, Reddit signal suite, replay fixture, and optional
  `posted_messages.json` retraction state. `.env.example` now includes every
  active V3 proxy/recheck switch (`PENDING_RECHECK_SECONDS`, `PROXY_MEDIA`,
  `PROXY_WARMUP_POST`, `EMBEDDIT_INSTANCE`, and `YOUTUBE_LINK_MESSAGE`), and
  the active workflows now pass the documented tuning Variables instead of
  leaving them as comments. Empty true-by-default Variables retain their code
  defaults, including the NSFW live-page fallback. The optional retraction
  cache is ignored locally so enabling it cannot leave an accidental
  working-tree file. The policy files now disclose the conditional Discord
  message-ID/payload cache and its retention purpose. See the
  [consolidated tracking record](REPOSITORY_TRACKING_2026-10-01.md).

* **2026-10-02 — Profile-crosspost and fallback observability hardening.**
  Reddit V3 now renders crossposts whose original is a user profile post from
  `/user/<name>/comments/...`, `/u/<name>/comments/...`, or Reddit's
  `/r/u_<name>/...` alias as
  `🔁 Crosspost of [u/<name>](https://www.reddit.com/user/<name>/) Profile`.
  Ordinary subreddit crosspost rendering is unchanged. A media-less vxReddit
  response whose normalized title is only `vxReddit` is now a fetch miss, so
  the fallback chain cannot use the mirror shell as a post title; a result
  carrying media is still accepted. A cached `TEST_TWEET_ID` keeps the exact
  existing dedup skip and now logs that the skip is intentional. This release
  adds offline fixtures for every profile route, the vxReddit shell, and the
  cache-skip invariant. No secrets, Variables, network request types, cache
  formats, retention, or data-processing behavior changed; the policy files
  remain current. See [Round 51 audit record](ROUND_51.md).

* **2026-09-30 — Runtime, delivery, and source hardening.** All executable
  workflows now pin stable CPython **3.14.8**; CI installs, compiles, and smoke-tests
  that exact interpreter before merge. Cache persistence uses an explicit
  `HEAD:<branch>` push, bounded rebase retries (15 s / 30 s), and clear failure
  annotations so a lost dedup update cannot be silent. The X fallback chain now
  starts with the tracker-healthy RSS hosts, while the Reddit chains include the
  current official Redlib registry's token-free non-Cloudflare mirrors. The
  standalone `CHANGELOG.md` was retired; this in-README section is the single
  release history. See [Python runtime policy](../PYTHON_RUNTIME.md) for the
  compatibility, performance, and update/automation policy.

* **2026-09-30 — Reddit V3 round 38e: RSS-backed native queue detection.**
  Token-authenticated public RSS `/new` listings are now the primary source for
  the negative-space mod-queue signal, with exact `pubDate` span parsing and
  URL-encoded reuse of the existing `REDDIT_FEED_TOKEN`. The prior HTML listing
  chain remains a fallback; unavailable or malformed data still fails open. The
  fetch is cached per subreddit for the run, does not add a setting or dependency,
  and new offline smoke coverage verifies IDs, dates, token wiring, and fallback-safe
  behavior.

* **2026-09-29 — Reddit V3 round 38d: native zero-comment mod-queue hold.**
  A post that is absent from a readable public `/new` listing can now be held
  even when it has no AutoModerator queue comment, but only when the post and
  listing ages prove it lies within the listing's visible span plus the
  existing six-hour window. The earlier positive-comment path is unchanged;
  an unparseable age, unavailable listing, or any other uncertainty fails
  open. The parser reuses existing post/listing fetches, the window remains the
  hard release cap, no workflow or repository Variable was added, and fifteen
  offline smoke checks cover the new and legacy paths.

* **2026-09-29 — Reddit V3 round 37: mod-queue gate.** Posts with positive
  AutoModerator queue evidence are held until they appear in the subreddit's
  redlib `/new` listing, then post exactly once. The gate requires both the
  queue-request comment and absence from `/new`; every uncertainty fails open,
  posts older than the six-hour window skip it, and holds use the existing
  `pending approval` short re-check. `MOD_QUEUE_GATE` and
  `MOD_QUEUE_WINDOW_SECONDS` are wired into the workflow; empty Variables keep
  the safe defaults. TEST POST and DRY RUN bypass the gate.

* **2026-09-29 — Reddit V3 round 36: settle window + duplicate-media gate +
  restore logging.** New posts wait through a configurable survival window; exact
  media already posted in the same sub is held with a posted-post-only winner;
  restores are logged loudly and pending records gain additive audit fields. Quiet
  runs add no calls, unknown duplicate identity fails open, and 35 smoke checks pin
  the behavior and wiring. Hotfix: empty GHA Variables (unset = empty string)
  fall back to the code defaults — the first deploy crashed on int("").

* **2026-09-28 — Reddit V3 round 35: NSFW content gate.** A BopLeaks ring
  post (`1ws8huc`) reached Discord while it was still live and was removed by
  Reddit seconds later. New posts are now checked in one batched Arctic Shift
  request against Reddit's `over_18` flag and `"nsfw"` thumbnail sentinel
  before media or webhook work. Flagged posts are held in the existing
  48-hour pending cache (`nsfw_flag`) and never posted; unknown metadata fails
  open, explicit test-post rebuilds bypass the gate, and the optional
  `NSFW_ALLOWLIST` repository Variable provides an emergency author/post-ID
  exception. Spoilers use a different field and remain untouched. Offline
  smoke coverage pins both NSFW markers, the clean/spoiler and fail-open
  paths, batching, pending behavior, allowlisting, workflow wiring and the
  main-loop guard.

* **2026-09-28 — Reddit V3 round 34: the dedup cache can no longer silently
  evict a subreddit's keys (AnantaLeaks re-post loop fixed + 4 new guards).**
  Live incident 2026-09-28: `AnantaLeaks_1wqhmw1` / `1wqphp3` / `1wriz86`
  posted to Discord on EVERY 5-minute cron run. Root cause (proven against
  the prod cache's commit history): `save_posted` capped the dedup cache at
  500 keys with `sorted(posted)[-500:]` — a LEXICOGRAPHIC eviction. Keys are
  `{sub}_{post_id}`, so once the six tracked subs crossed 500 total keys, the
  alphabetically-first sub — `AnantaLeaks_*` sorts before Genshin / Honkai* /
  WutheringWavesLeaks / Zenlesszonezeroleaks — was evicted on every save:
  added right after posting, dropped in the same save, missing from the next
  run's dedup check, re-posted, forever (each save's visible "1 deletion" was
  the oldest Genshin key — those posts are outside the 48 h feed window, so
  their loss was invisible). Now: retention is **per-subreddit, newest-first**
  (`MAX_CACHE_SIZE_PER_SUB`, default 250 — leet post ids sort chronologically
  within a sub) with a generous global backstop (`MAX_CACHE_SIZE_TOTAL`,
  default 10 000). Extra guards: (1) keys posted THIS run are force-kept by
  the save (`keep_newest` belt and braces); (2) the posting loop re-checks
  the dedup cache right before the expensive pipeline (a key listed twice in
  one feed batch can no longer post twice; TEST POST rebuilds exempt); (3) a
  per-run flood cap (`MAX_POSTS_PER_RUN`, default 25) posts the newest 25 and
  loudly logs the rest — any future cache loss causes one capped run, not an
  all-night re-post storm; (4) after every save the script verifies the
  just-posted keys are on disk and logs a `DEDUP GUARD` error if any are
  missing — this failure mode can never again be silent — plus a load-time
  saturation warning. 18 new offline smoke checks (11 Reddit + 7 X) pin the
  retention rules. The SAME latent bug was found and fixed in the X engine
  (twitter_v3.py): its cache keys are `{account}_{tweet_id}` too, so at the
  cap `Ananta_EN` would have been the victim; its "keeps the NEWEST 500"
  comment was factually wrong (the cache was at ~143/500 when this landed —
  ~2–3 weeks of headroom at current volume). No secrets touched; the new
  knobs are optional repo Variables; the P0 double-post concurrency rule is
  unchanged. See the round-34 section under the Reddit monitor.

* **2026-09-25 — Reddit V3 round 33: URL-labelled links render clean (live
  1wpejir + 1wpdxhs).** Two ZZZ showcase posts ended with a well-formed
  markdown link whose LABEL is a bare URL and whose TARGET differs —
  `[https://zzzanalytics.vercel.app/](https://www.youtube.com/redirect?…)`
  (the author copied the link from a YouTube video description; YouTube
  wraps it in a `youtube.com/redirect` URL with a ~330-char token). The
  Discord card printed the raw link literally — label, brackets and the
  whole redirect blob (Reddit rendered it fine, label only). Rounds 15–22
  intentionally leave descriptive links untouched (round 22 unwraps only the
  self-referential `[U](U)` class), so this class had no handler. Now (same
  clean-line pre-pass, round 22's identical mangle-residue guard): a
  URL-labelled link collapses to the bare URL (Discord auto-links it — for a
  redirect-wrapper target the label is the real site, i.e. the better link);
  a prose-labelled link whose target is a `youtube.com/redirect` wrapper
  becomes `label (decoded destination)` via the wrapper's `q=`/`qp=` param.
  Everything else byte-identical (prose-labelled descriptive links, mangle
  residue, `[U](U)`, all gates, dedup, caches, concurrency). 8 new offline
  smoke checks pin the live shape end-to-end. See the round-33 section under
  the Reddit monitor.

* **2026-09-20 — Reddit V3 round 32: queued posts can no longer post early
  + reason-aware pending re-check.** Live incident: post `1wl41aj` ("Post
  is awaiting moderator approval.") was posted to Discord ~1 cron tick
  after creation while still queued — the RSS feed delivers queued posts
  with real content, and the round-20 liveness gate was Arctic-only. Now:
  the liveness gate runs for ALL sourced posts (RSS candidates verify
  against the proxies + redlib post pages ONLY — the feed cannot verify
  the feed); the mod-queue banner is an explicit reason (`pending
  approval`); `not_live` / `pending approval` / `sources_down` re-check on
  the new short `APPROVAL_RECHECK_SECONDS` interval (default 300 s, repo
  variable) — a newly-approved post posts on the next cron tick instead of
  waiting up to 30 min; removed/deleted reasons NEVER re-check (a restored
  post re-enters via RSS with a fresh `updated` stamp and posts normally —
  this also kills the 15–20 min zombie runs from the 2026-09-20 logs);
  `media_wait` / `partial_gallery` keep the round-30 30-min throttle.
  16 new offline smoke checks. Stdlib only, no new secrets; posting path
  otherwise byte-identical; the P0 double-post concurrency rule is
  unchanged. See the round-32 section under the Reddit monitor.

* **2026-09-20 — Reddit V3 round 31: the feed-token `.json` probe is skipped
  when there's no OAuth app (65 s of guaranteed 403s removed).** Live
  2026-09-20 audit: the round-12 FULL-MODE probe (feed token on
  `comments/<id>.json`, 65 s `FEEDTOKEN_JSON_STAGGER` wait) 403s from
  datacenter IPs while no Reddit OAuth app exists — 65 s of log noise per
  run with new posts, never a real fallback. New `REDDIT_JSON_PROBE` repo
  Variable: `auto` (default) = probe runs only when BOTH `REDDIT_CLIENT_ID`
  + `REDDIT_CLIENT_SECRET` are set; `force` = legacy always-try (65 s per
  run with new posts); `off` = never. The workflow now maps the two OAuth
  secrets LIVE (empty = harmless), so future FULL MODE = just set the two
  secrets — no code or workflow change. Runs: 213 s → ~148 s (18-post first
  run), 121 s → ~56 s (3-post run); steady-state zero-post runs (7 s)
  untouched. 6 new offline smoke checks (probe-mode logic). Nothing else
  changed: RSS, proxies, Arctic, YouTube, crossposts, liveness/removal
  gates, pending-cache re-check — all exactly as before. See the round-31
  section under the Reddit monitor.

* **2026-09-19 — P0 double-post fix (shipped alongside round 29):**
  `concurrency` guard in both production monitors
  (`check-reddit-<branch>` / `check-twitter-<branch>`,
  `cancel-in-progress: false`) — a 2nd trigger now QUEUES and checks out
  the first run's fresh dedup cache instead of posting the same items
  twice (2026-09-19 AnantaLeaks_1wkld9d / WutheringWavesLeaks_1wkldhu /
  AnantaLeaks_1wkle5u double post). Cancelling stays disabled: a run can
  sit between "Discord posted" and "cache committed".

* **2026-09-19 — Reddit V3 round 30: pending cache — skipped posts are
  remembered, re-checked live on a 30-minute throttle, and never cached as
  posted.** Posts skipped for a transient reason (mod-queue pending
  approval, soft removal that may be restored, media still missing /
  partial gallery) now land in `pending_reddit.json` (auto-committed with
  the other caches). The next runs re-check them live — the throttle sits
  before any network work for that post — with a per-post
  `PENDING_RECHECK_SECONDS` wait (default 1800 s); a post that posts
  normally is cleared from the pending cache. Removed/deleted posts stay
  unposted and un-cached as before. The X cache dump is also sorted, so an
  identical id set produces byte-identical JSON (no junk cache commits).
  Offline smoke checks cover the throttle, the four skip gates, the
  pending save paths, the sorted X cache and the workflow concurrency
  groups.

* **2026-09-19 — Reddit V3 round 29: crosspost card cleanup — the
  mirror's crosspost notice is no longer the body, one photo listed
  twice under different URLs is one tile, and the 🔁 line is always
  shown.** (Live: `AnantaLeaks/1wjv962`, a crosspost of
  `AnantaStation/1wjv8r7` — "Lemon Recording Studio via Dremka".)
  A crosspost's own text is EMPTY, so the mirror (redditez/EmbedEZ)
  filled the card's body with its crosspost *notice* — `Original
  PostPosted in r/AnantaStationLemon Recording Studio via Dremka`
  (notice fragments glued without spaces + the original's title) —
  and listed the same single photo TWICE (two og:image redirect URLs
  for `content.media.0` / `content.media.1`, both resolving to the
  same `i.redd.it` file). The 🔁 line was missing too: the post was
  too new for any permalink (no "crosspost" link in the RSS body,
  Arctic not captured yet). Now:
  1. **Notice stripping** (`_crosspost_notice_clean`): a body that is
     ONLY the mirror's crosspost notice ("posted in r/…" / "Crosspost
     of [Sub](url)" fragments, with or without the original's title
     glued on) is removed — real body text is never touched, and a
     mere "original post" mention alone is left alone (weak evidence
     never triggers).
  2. **Crosspost line fallback:** when the notice names the original
     subreddit and no permalink is available anywhere, the card still
     gets `🔁 Crosspost of [r/Sub](https://www.reddit.com/r/Sub/)
     Subreddit`; a permalink handed back markdown-wrapped as
     `[url](url)` is unwrapped to the bare URL. Clean crossposts render
     the byte-identical old line.
  3. **Same-file media dedupe** (`_dedupe_media_final_urls`): before
     the gallery cap, redirect-style media URLs are resolved (HEAD,
     follows redirects, 8 s best-effort) and only the first item per
     final file is kept — a photo served under two wrapper URLs is one
     tile. Applies to EVERY source (proxy/redlib/RSS/Arctic); a URL
     that fails to resolve is never dropped.
  14 new offline smoke checks (section 6) cover notice stripping,
  dedupe and the header lines. The approved Ananta2027 card (🔁 line,
  unique media, clean body) is the reference for all future
  crossposts, all subreddits.

* **2026-09-18 — X V2/V3 round 28: bogus "Translated from French" cards +
  broken non-ASCII hashtag links (two live bugs, one fix each).**
  1. **Language mis-detection guard:** X's per-tweet `lang` is an automatic
     guess — live misfire 2026-09-18: `2100794014630846965` ("Maintenance 🩸"
     + hashtags, from an ESP/ENG artist) was tagged `fr` and `/en` returned a
     "translation" identical to the original, so the card showed
     *🌐 Translated from French* for text that never changed. V2/V3 now
     compare the `/en` translation to the original
     (`translation_is_identical`, case/whitespace/punctuation/emoji-insensitive):
     identical → no block, posted as-is, logged (`/en translation is
     identical to the original — X language mis-detection`); different → the
     "Translated from X" block exactly as before, so real Japanese/English
     cards are unaffected. V1 unchanged (documented).
  2. **Non-ASCII hashtags:** some artists embed non-ASCII characters in tags
     (the same post's `#zzzero` carries U+3164 HANGUL FILLER: `zzzeroㅤ`).
     `linkify_text` captured the full tag (correct) but built a URL with the
     raw character, which Discord's markdown parser rejects, so the card
     printed the literal `[#zzzero  ](https://x.com/hashtag/zzzero )`.
     Hashtag URLs are now percent-encoded
     (`https://x.com/hashtag/zzzero%E3%85%A4` — the exact page X itself links
     to); pure-ASCII tags are byte-identical, and accented tags
     (e.g. `#célébration`) now link too. @mentions unchanged.

* **2026-09-18 — Reddit V3 round 25: most-complete-media-wins (1wj0p83).**
  Proxy chain keeps the largest eligible media list (priority breaks ties;
  20-item capacity stops early and caps the returned list without mutating
  the source result). Known partial archive galleries skip without
  caching and retry within the freshness window. Adds offline regression tests
  for 1-vs-13 images, ties, fallback, video, capacity, health and archive gates.

* **2026-09-18 — Reddit V3 round 24: redlib.miningtcup.me joins the
  redlib fallback fleet.** miningtcup (the nitter-RSS-token operator)
  also hosts a redlib instance; it now sits in `REDDIT_RSS_INSTANCES`
  (after the two reddit.com hosts, ahead of the Anubis-lottery
  instances) and gets the miningtcup token appended as `?token=` via
  the new `_with_miningtcup_token` helper at both chokepoints
  (`_fetch_feed` + `_fetch_redlib_post_page`). `reddit_monitor_v3.yml`
  now wires the SAME existing `NITTER_RSS_TOKEN` repo variable. If the
  WAF doesn't accept the token there, the instance logs a bot-check
  miss and the chain moves on — no behavior change. `inv.miningtcup.me`
  (Invidious) was checked the same day: up (v2026.09.13) but video
  fetch broken (Invidious error page on `/watch`) — not wired in.
* **2026-09-18 — Reddit V3 round 23: media must win the proxy chain (the
  1wj38fc gallery) + removal-notice variants.** `AnantaLeaks/1wj38fc`
  (2-photo spoilered gallery) posted media-less and was cached that way:
  at +6 min vxreddit served title/stats/body but no og:image yet, and the
  old chain rule accepted that text-only result as "usable" and stopped
  the chain before embeddit (which DID have the photos) was tried. Now:
  (1) `fetch_proxy_post` returns the first service with media — a
  text/stats-only result is kept as fallback and the chain continues;
  (2) an Arctic record that positively says a post has media (gallery
  flags / `post_hint` / redd.it media URL) but had none served this run
  is skipped and NOT cached — the next run retries (48h window bound),
  so the full gallery posts once the media is available. 22(b): a whole
  title of `[ Removed by moderator ]` is now a removal marker, and the
  moderators notice also catches "removed by Reddit's filters."
* **2026-09-18 — X V2/V3 round 14: miningtcup RSS token live (sent two
  ways).** The emailed token for the token-gated `nitter.miningtcup.me`
  instance is now sent as the `Authorization: Bearer` header **and**
  inside the `User-Agent` (the operator confirmed the token is accepted
  anywhere in the UA; the round-12 `?token=` query param is kept) — both
  V3 and V2. Put it in the existing repo variable `NITTER_RSS_TOKEN`;
  the next run picks it up. Credits: miningtcup.
* **2026-09-17 — X V2 catch-up: rounds 11 + 12 backported from V3** (V2 is
  the standby engine — `twitter_monitor.yml` still runs V3, so live output
  is unchanged):
  * **Round 11 — tweet-data fallback chain.** V2 now uses the shared
    `twitter_proxy` chain (FxTwitter → fixupx → vxtwitter → twitterez)
    via a soft import, so it no longer depends on FxTwitter alone. The
    `/en` translation call is now attempted only when the data really came
    from FxTwitter (the backup services have no `/en` endpoint), and the
    winning service is logged as `source=...`.
  * **Round 12 — nitter fleet.** V2's `RSS_INSTANCES` was still the old
    4-instance list (all stale/dead in round 12's probes); it now uses the
    same refreshed 11-instance fleet as V3. Every attempt is logged per
    instance, a dead fleet raises `NO working nitter instance` /
    `ALL FEEDS FAILED this run`, `NITTER_RSS_TOKEN` unlocks the
    token-gated instance, and `TEST_TWEET_ID` can rebuild one tweet
    nitter-free.
  * **Bugfix found while porting:** V2 computed the first-run limit
    (`entries`) but then iterated `feed.entries`, so a first run posted
    *every* feed entry instead of just the newest. It now iterates
    `entries`, matching V3.

* **2026-09-17 — round 13 (X V3): repost attribution** — a reposted tweet
  now shows `[<account> reposted](https://x.com/<account>)` in the header
  (e.g. `[TYPEII_EN reposted](https://x.com/TYPEII_EN)`) plus a
  `📌 Original:` line naming the true author, instead of impersonating the
  original author's own tweet. Detected from the feed itself (author from
  the tweet-data API ≠ feed account — FxEmbed's `reposted_by` field only
  works with the retweet's own id, which nitter RSS doesn't carry); Read
  Post, stats, translation and media are unchanged.

* **2026-09-17 — round 12 (X V3): nitter fleet resilience + visible failures
  + TEST_TWEET_ID + RSS-token support** (the X monitor silently no-oped on
  2026-09-17 — every known nitter instance was dead/stale and that path
  logged nothing; missed tweets included
  `Wuthering_Waves/2100555373073797461`):
  * Every nitter attempt is now logged per instance; `NO working nitter
    instance` / `ALL FEEDS FAILED this run` make a dead fleet loud.
  * `RSS_INSTANCES` expanded to the WHOLE tracked fleet — 11 instances,
    ordered by live 2026-09-17 probes (`jaydenha.uk` + `meowing.monster`
    verified fresh first; `xcancel.com` suspended but kept, auto-revives if
    it returns).
  * RSS-token support: `nitter.miningtcup.me` is behind a bot check — set
    the emailed token as repo variable `NITTER_RSS_TOKEN` (sent as Bearer
    header + `?token=`) and the next run picks it up, no code change.
  * `TEST_TWEET_ID` / workflow `test_tweet` input: rebuild ONE specific
    tweet nitter-free through the same pipeline + cache.
  * GitHub's native `schedule:` disabled in both monitor workflows
    (cron-job.org = single scheduler — the race caused the 2026-09-17
    `1wis2u5` double post), with a re-enable note.
  * Next cron-job.org run auto-posts the 2026-09-17 catch-up: WW song
    credits (video) + 08:00 wallpaper, TYPEII_EN's @zeroartwo repost,
    Ananta_EN 11:37 giveaway-winner announcement.

* **2026-09-17 — round 22 (Reddit V3): clean auto-linked links stay raw**
  (same-day follow-up — the 1whe2tr re-test ON THE NEW CODE still showed
  `Firefly video [https://b23.tv/…](https://b23.tv/…)`): the post's bare
  URLs can also arrive from a source that AUTO-LINKS them, as a CLEAN
  markdown link (`label [U](U)`). Round 21 intentionally left clean
  links untouched — but the components-v2 card renders the body as
  PLAIN TEXT, so a link whose text is its own URL showed its literal
  brackets. Round 22 collapses URL-labelled links (text == URL) to the
  bare URL:
  * `Firefly video [https://b23.tv/…](https://b23.tv/…)` →
    `Firefly video https://b23.tv/…` (the original line; mangle faces,
    raw pairs and standalone URL lines behave exactly as round 20/21).
  * The repaired mangle family (round-15 cascade) now outputs the bare
    URL too, so every label+URL face renders identically.
  * Descriptive links (`[text](URL)` with text ≠ URL) and prose stay
    byte-identical; lines with mangle residue are untouched by the new
    step.
  * Smoke test: the round-15 URL-labelled/cascade checks now pin the
    raw output + 4 new round-22 checks (`tests/test_smoke.py` — 226
    total).

* **2026-09-17 — round 21 (Reddit V3): raw plain links** (follow-up to
  the round-20 live run — the card body should match the ORIGINAL post
  as raw text):
  * **Mangle output is now raw:** the round-20 fix outputs
    `Firefly video https://b23.tv/…` — label + the bare URL exactly
    once, no markdown wrapping (renders identically: Discord auto-links
    the bare URL in the component v2 container).
  * **Clean "label / URL" pairs collapse to one raw line:** a bare URL
    line under a plain label line (the original post's shape, with or
    without a blank line between) becomes `label https://…` — the same
    look mangled posts get, so all label+URL posts render identically.
  * **Standalone URL lines stay raw:** no longer wrapped in markdown —
    Discord auto-links them (YouTube-line removal, redd.it media URL
    removal and every other body rule are unaffected).
  * Smoke test: the round-20 link checks now pin the raw output, plus
    5 new label/URL-pair + standalone-URL checks (`tests/test_smoke.py`
    — 222 total).
  * Nothing else changed: RSS, proxies, FULL MODE, YouTube, crossposts,
    the liveness gate and the round-18 removal filter all run exactly
    as before.

* **2026-09-17 — round 20 (Reddit V3): archive liveness gate + the simple
  plain-link fix** (follow-up to the round-19 live run):
  * **Archive (Arctic) posts are now verified live before posting.**
    The archive keeps posts that are no longer live on reddit — removed
    by moderators, deleted by the author, or still pending approval in a
    mod queue — and its stored body is often the ORIGINAL content, which
    is why the removal-notice filter could not catch them. An
    archive-sourced post is now only posted when a live source (redditez
    → vxreddit → embeddit, then redlib) can actually retrieve it;
    otherwise it is skipped and NOT cached, so it posts normally once
    approved or restored. Log line: `[<sub>_<id>] archive post not
    verified live (…) — skipping, not cached (will post once
    approved/restored).` RSS-sourced posts and TEST POST rebuilds are
    unaffected.
  * **The link fix is now the simple one** (replaces the round-19 rule):
    any mangle face — `label [[U](U)](U](U))`, `label [U](U](U))`, or
    deeper nesting — collapses to ONE plain line with the URL exactly
    once: `label [U](U)`, exactly like the original post (auto-links
    itself as a blue clickable link in the component v2 container).
    Clean links, repeated real links, bare-URL lines and every round
    15/16 shape are byte-identical.
  * Smoke test: 11 new checks (4 liveness-gate + 7 link; the round-16
    mangle check returns to its original same-line expectation —
    `tests/test_smoke.py` — 219 total).
  * Nothing else changed: RSS, proxies, FULL MODE, YouTube, crossposts,
    the round-18 removal filter all run exactly as before.

* **2026-09-17 — round 19 (Reddit V3): 'label line + bare URL' link mangle
  repair** (follow-up to the round-18 live run — post 1whe2tr):
  * The feed's auto-linker mangled bodies made of "label line + bare URL
    line" pairs (e.g. `Firefly video` / `https://b23.tv/…` / `Feixiao
    video` / …): it doubled/tripled the opening `[` of the URL-labelled
    link, glued `](U](U))` tail fragments on, and duplicated the next
    label's first word as a dangling `Word](U](U)` line — the card showed
    nested `[[U](U)…](U](U)…` garbage instead of clickable links.
  * A new pre-pass in **both** body cleaners (RSS path and proxy path)
    repairs the family to **one label line + one clickable URL line per
    pair** — the look of the X cards. Every other line shape is
    byte-identical to before; the round-15/16 mangle repairs are
    unchanged.
  * The round-16 smoke check's expected output was updated to this same
    label+URL-line format (it is the same mangle family, now rendered in
    the target layout).
  * Smoke test: 6 new checks (`tests/test_smoke.py` — 214 total).
  * Nothing else changed: the round-18 removal filter, cache, proxies,
    media, FULL MODE, YouTube and crossposts all run exactly as before.

* **2026-09-17 — round 18 (Reddit V3): soft-removed / deleted post filter**
  (follow-up to the round-17 live run):
  * The archive (and occasionally RSS) still carries posts the moderators
    soft-removed or the author deleted, with a removal-notice body —
    `"[deleted]"`, `"[removed]"`, `"**[ Removed by moderator ]**"`,
    `"Sorry, this post has been removed by the moderators of r/…"`,
    `"Sorry, this post was deleted by the person who originally posted
    it"`. These are now detected and **skipped** (round 17's first live
    run posted a few such cards, which had to be deleted from the channels
    manually).
  * Skipped posts are **not added to the dedup cache** — if a post is
    approved later it surfaces again (RSS or archive) and posts normally.
  * Explicit `TEST_POST_ID` rebuilds are unaffected; every skip is logged:
    `[<sub>_<id>] post appears removed/deleted (<reason>) — skipping, not
    cached (will post once approved).`
  * Smoke test: 9 new detection checks (`tests/test_smoke.py` — 208 total).
  * Nothing else changed: RSS, proxies, FULL MODE, YouTube, crossposts and
    the round-17 archive backup all run exactly as before.

* **2026-09-17 — round 11 (X V3) + round 17 (Reddit V3): tweet-data
  fallback chain, GIF chain restructure, Arctic Shift search backup:**
  * **X V3 tweet-data fallback chain** (new `testing area/twitter_proxy.py`):
    **FxEmbed/FxTwitter** (primary) → **fixupx** (same engine, stand-by
    host) → **vxtwitter** (BetterTwitFix API — multi-photo tweets as
    separate photos) → **twitterez** (EmbedEZ bot page — ad lines
    stripped, video posters not duplicated). Every result is normalized to
    the FxTwitter shape, so cards are identical no matter which service
    answered; the winner is logged per tweet. `/en` translation only when
    the data came from FxTwitter.
  * **X V3 GIF chain restructured:** `gif.fxtwitter.com` `.webp` →
    `gifconvert.vxtwitter.com` `.webp` → `.gif` (browser-Referer probe) →
    fastgif (offline 2026-09-17 — last probe, auto-revives if it returns).
    `.avif` intentionally not used (Discord's gallery can't render it).
  * **Reddit V3 Arctic Shift search backup:** subreddits with no new RSS
    posts are re-checked via the archive's `/api/posts/search` (same post
    shape as the crosspost lookup); archive posts run through the same
    `collect()` (dedup + 48h window unchanged); soft-fail + shared circuit
    breaker.
  * **Smoke test:** first functional checks for the X V3 data path — GIF
    chain order/probes, vxtwitter normalization (GIF, multi-photo, quotes),
    twitterez og-page parsing (stats incl. `1.5M`, ad lines, posters),
    fallback-chain order, Arctic search params/failures + entry shim
    (40 new functional checks + the import gate — 199 total).
  * **Docs updated:** this entry, the round-11/round-17 sections, credits,
    troubleshooting, `docs/CI_SMOKE.md`, `PRIVACY_POLICY.md`,
    `TERMS_OF_SERVICE.md`. **Untouched:** `twitter_v1.py`,
    `twitter_v2_button_outside.py`, both workflow yml files,
    `.env.example`, `.gitignore`, `requirements.txt` (no new secrets,
    dependencies, or files at runtime).

* **2026-09-16 — round 14 (Reddit V3 card polishing, after the first
  production runs):**
  * **Complete galleries incl. GIFs** — the redlib post-page harvest now
    runs in parallel with the proxy fetch and its complete ordered list
    wins for image posts (redditez og: tags omit GIFs; a 6-item post showed
    3 before). Video posts skip the harvest; all-proxies-down still gets
    the redlib list.
  * **Gallery dedupe** — the proxy embed pages' extra `og:image` tags (the
    "main image", 140px crops, same-photo second rendition) are dropped by
    the new `dedupe_proxy_media` in `reddit_proxy.py`.
  * **Body formatting like the redditez card** — clickable markdown links
    for all links, `**bold**` + paragraph breaks kept, bare redd.it media
    URLs removed from the text (fixes the glued-URL bug), og: values
    unescaped until stable (fixes `&amp;amp;`).
  * **Crossposts keep working** — the crosspost notice in the RSS content
    is detected; media/stats are fetched from the ORIGINAL post; the card
    keeps the crosspost URL + "🔁 Crosspost of" line.
  * **Stats backfill** — when the winning proxy has no stats (common with
    redditez), the 💬/👍 row is backfilled from the Embeddit JSON (~1 s).
  * **Embeddit plain-text shape** — unmarked-up content ("Title⬆️ 1.1K
    • 💬 108") and compact numbers are parsed.
* **2026-09-16 — round 13 (Reddit V3 proxy media services + docs):**
  * **Proxy media path (native mode):** card media now comes FIRST from the
    public proxy services — **redditez.com (EmbedEZ) → vxreddit.com →
    embeddit.deltandy.me** in that priority order (new module
    `testing area/reddit_proxy.py`, keyless public APIs — no credits, no
    API key). The winning service's own URLs are used verbatim in the
    components-v2 card: **full-res photos, EVERY gallery photo (up to 20 =
    2 containers), videos WITH audio, GIFs, plus 💬/ stats**. This fixes
    the native-mode gaps from round 12: multi-photo galleries now post all
    photos (the RSS content only inlines one), videos use each service's
    muxed mp4 (with audio) and are range-checked before use, and any-age
    test posts resolve from any service (post JSON 403 / outside the
    100-entry feed window no longer matter).
  * **Warm-up link test:** every run probes all three services in parallel
    with one known post (default `HonkaiStarRail_leaks/1whbjbh`, override
    `PROXY_WARMUP_POST`) and writes **`proxy_health.json`** (auto-committed
    with the cache). Services proven dead are skipped for the run — unless
    all three are dead, in which case every service is retried per post.
    When a redditez page shows *"Failed to Get Post | EmbedEZ — Reddit
    returned a non-JSON response"* it means the EmbedEZ backend (redditez's
    engine, which fetches the post from Reddit for us) is down or
    unavailable at that moment — a service-side failure detected **per
    post** — and the post falls through to vxreddit/embeddit (the two most
    uptime-reliable).
  * **Native path kept as final fallback:** if every proxy fails for a
    post, the round-12 native RSS path (RSS media → redlib harvest →
    thumbnail) runs unchanged. `PROXY_MEDIA=0` disables the proxy path
    entirely. FULL MODE (OAuth app) is untouched.
  * **YouTube second message:** posts containing a YouTube link now also
    send a **second, plain message with only the YouTube link** after the
    card lands (Discord shows the official preview; no buttons). The card's
    own YouTube thumb + animated `starwardspark3` button stay.
    `YOUTUBE_LINK_MESSAGE=0` disables the second message.
  * **Crossposts + 20-photo galleries:** unchanged — proxies return the
    crosspost's own content (RSS/native paths still follow the original),
    and 11–20 media items still render as **2 containers** (10 items each).
  * **Docs:** new `docs/DISCOHOOK.md` (what Discohook is/does here —
    **preview-only, fully optional, safe to disable**, and why it isn't
    relied on for posting) and `docs/CI_SMOKE.md` (ci.yml + test_smoke.py
    are the **required** offline safety gate — what they catch and why
    auto-merge waits on them); `docs/DEPENDABOT.md` gains the
    **Node 20 → 24** explanation (the deprecation warning vanished because
    Dependabot auto-bumped `actions/checkout`/`setup-python` to v7).
  * **Workflow:** `actions/checkout@v7` + `actions/setup-python@v7`
    (Node 24 runtime, matches the verified 2026-09-15 run log); auto-commit
    now also commits `proxy_health.json`; `EMBEDEZ_API_KEY` no longer
    needed by V3 (the keyless proxy endpoints replaced the paid API — the
    secret can be deleted; only old V2 uses it).

* **2026-09-15 — round 12 (Reddit V3 polish, from live test-channel review):**
  * **All photos now post (native mode):** the RSS content is scanned for
    every `redd.it` media URL in post order; single-image posts no longer
    show only the 140px thumbnail. (FULL MODE already had all photos.)
  * **Gallery posts (native mode):** multi-image posts carry no image links
    in the RSS content (verified in the live 2026-09-15 workflow log), so
    the post page is now harvested from the redlib fallback instances in
    parallel — same lottery as the feed, ~10s worst case, thumbnail kept on
    failure.
  * **Best rendition per photo:** `i.redd.it` full-res swap for jpg/jpeg
    (slug-prefixed preview names reduced to the bare file id) or the largest
    signed preview URL — the 140px feed thumbnail is no longer used.
  * **Body cleanup:** stray `redd.it` image URLs stripped from card text.
  * **Video posts = video only:** duplicate first-frame /
    `external-preview.redd.it` screenshots dropped whenever a video resolves
    (also fixes YouTube posts that showed a screenshot tile + video).
  * **Native video chain:** `v.redd.it/<id>/DASH_<q>.mp4` (self-contained mp4
    **with audio**, no proxy/sig/expiry) now tried before the embedez/vxreddit
    CMAF muxing proxies; signed `packaged-media.redd.it` masters deliberately
    avoided (they expire in hours).
  * **YouTube default = thumbnail + animated `starwardspark3` button**
    (the old `▶️` emoji is gone from V1/V2 buttons too); playback attempt
    (seaof.glass) moved behind `YOUTUBE_MEDIA_EMBED=1`; thumb chain
    maxres→hq→mq.
  * **💬 OP comment (FULL MODE):** stickied/top OP comment fetched with the
    post JSON (`limit=25`) and shown capped (500 chars) with a full-comment
    link; `REDDIT_OP_COMMENT=0` disables. Total text is now budgeted under
    Discord's 4000-char limit.
  * **Discohook preview (keyless):** per-card share link rendered from the
    exact payload, logged to the workflow run; webhook URL never sent to it;
    `DISCOHOOK_PREVIEW=0` disables.
  * **Test tools:** workflow `test_post` input (`<sub>/<post_id>`) + `dry_run`
    (payloads logged, Discord/cache untouched) for verifying before
    promoting; `FEEDTOKEN_JSON_STAGGER` made configurable.
  * **Dependabot + CI safety chain (all optional but shipped):**
    `.github/dependabot.yml` (weekly PRs, delete to disable), `ci.yml`
    (install + compile + offline smoke test gate on every PR),
    `dependabot_auto_merge.yml` (opt-in auto-merge, green checks required,
    enabled only via the `AUTO_MERGE_DEPENDABOT=yes` variable),
    `tests/test_smoke.py`, and full user-facing docs in `docs/DEPENDABOT.md`.
  * **Docs:** README V1/V2/**V3** comparison + V3 behavior, optional-variable
    table, Discohook + Dependabot sections; `.env.example`, privacy policy
    and ToS updated for the new third parties.
* **2026-09-13 — round 10:**
  * **Full X Article support (V2/V3)** — article tweets now post cover image + **title** + full
    body text + in-article images/GIFs (GIFs animated via the existing gif.fxtwitter → fastgif
    chain; in-article videos get the same size handling), all from FxTwitter's `tweet.article`
    JSON — no scraping, no login. Verified live (HonkaiNA DevTalk article; log shows
    `| article`). FxTwitter doesn't translate article bodies, so non-English articles post in
    their original language (normal tweets still get `/en`).
  * **Video gallery limit live re-verified** with a one-off diagnostic card
    (`testing area/video_diag.py`, safe to delete): 171 MB & 234 MB tiles **play** in every URL
    style; 521 MB+ **fail** ("image not found") in every style → the 256 MB default confirmed in a
    proven-safe gap; `?tag` param and proxy origin proven irrelevant to playability.
  * **New `GALLERY_VIDEO_LIMIT` safety cap** (default `0` = off, behavior unchanged): optional
    extra gallery ceiling that auto-downgrades to the largest fitting variant (**all** variants
    checked) or posts a "watch on X" note — the gallery can never embed an unplayable tile when
    enabled.
  * **Docs:** "image not found" recovery steps (transient Discord proxy failure on old messages —
    delete message + remove its cache line + re-run; re-posting always works).
  * **X V1 (`twitter_v1.py`, formerly `main.py`)** — default `ACCOUNTS` list now includes `Ananta_EN` (matches V2/V3);
    header comment tidy-up only. No behavior changes.
* **2026-09-13 — round 9:**
  * **Reddit reliability (live-verified):** primary fetch is now **ONE combined feed request**
    (`/r/sub1+sub2+.../new.rss?limit=100`) covering all subreddits — fits Reddit's
    ~1 req/min anonymous datacenter limit; automatic per-subreddit fallback kept. `?limit=100`
    verified (default 25, max 100).
  * **New `REDDIT_FEED_TOKEN` secret** (optional, recommended): personal feed token
    (old.reddit.com → Preferences → Feeds) appended as `?feed=…` → logged-in rate tier.
  * **Fallback mode:** two 429 retries (6s + 45s) instead of one; instance list trimmed to 5
    responding sources after live-probing **every** official Redlib registry instance + eddrit —
    all behind Anubis/Cloudflare/gammaspectra bot challenges or dead (fallback lottery only).
  * **Docs:** new Testing Area guide (quotes required for `testing area/` paths) + guidance comments
    inside both workflow ymls; X `RSS_INSTANCES` retested and intentionally unchanged.
* **2026-09-12 — round 8:**
  * **Reddit RSS sources fixed for multi-sub monitoring.** `redlib.perennialte.ch` removed (shut
    down 2026-08-31, now answers HTTP 410); fresh Redlib fallback chain from the official
    [redlib-instances](https://github.com/redlib-org/redlib-instances) list (safereddit.com,
    red.artemislena.eu, redlib.privacyredirect.com, redlib.privadency.com, redlib.nadeko.net,
    redlib.ducks.party, redlib.catsarch.com, snoo.habedieeh.re). **429 retry with 6s backoff** +
    **staggered fetch starts (1.2s)** so six subreddits no longer hit www.reddit.com in the same
    second — fixes the "only one subreddit posts per run" symptom.
* **2026-09-12 — round 7:**
  * **Five new default subreddits** added to both Reddit engines:
    `Genshin_Impact_Leaks`, `HonkaiStarRail_leaks`, `WutheringWavesLeaks`, `HonkaiNexusAnimaLeaks`,
    `AnantaLeaks` (all verified live/active). Matching per-sub secrets
    (`WEBHOOK_REDDIT_GENSHIN_IMPACT_LEAKS` … `WEBHOOK_REDDIT_ANANTALEAKS`) documented, and the
    sample `reddit_monitor_v3.yml`/`.env` updated.
  * **Switchable V1 embed mirror:** new optional **`REDDIT_MIRROR`** repo Variable — `redditez.com`
    (default), `embeddit.deltandy.me`, or `vxreddit.com`. All three were verified live to accept
    the same post path and serve embed meta to Discordbot. Host normalization tolerates full URLs.
    Reddit V2 is unaffected (EmbedEZ API builds the card itself).
* **2026-09-12 — round 6:**
  * **GIF resilience — fastgif fallback added.** With `gif.fxtwitter.com`'s CDN still down
    (530/1033), GIF posts were falling back to mp4 players. GIFs now resolve through a two-source
    probe chain: the official `gif.fxtwitter.com` WebP first, then
    **fastgif** (`fastgif-production.up.railway.app/tweet_video/<id>.gif`) — an independent
    third-party converter serving REAL animated GIFs that show *and* play in Components V2
    (confirmed live against the exact tweet ids that were broken). Only its `.gif` route is used —
    its `.webp` route errors, and unknown ids return 500, so the probe is safe and never forced.
    If neither converter answers, the original mp4 is kept (still plays as a video). The chain
    self-heals in both directions. Verified live on single-GIF and 4-GIF tweets.
* **2026-09-11 — round 5:**
  * **Portrait-video handling revised** after further evidence: the "loads but won't play" symptom
    is a transient Discord proxy warm-up (the same direct URLs soon play fine in Components V2), so
    the round-4 proxy wrap is retracted to an opt-in `PORTRAIT_PROXY` toggle (default **off**) —
    direct URLs for all videos, zero extra load on FxTwitter.
  * **Ananta_EN added** to tracked accounts (default list, README routing table, workflow env,
    .env example). Remember: a new account needs its `WEBHOOK_ANANTA_EN` secret *and* the matching
    `env:` line in the workflow, plus `Ananta_EN` appended to the `ACCOUNTS` secret.
* **2026-09-11 — round 4 (quotes, GIFs, articles, portrait fix):**
  * **Fixed both live `400 {"components": ["0"]}` failures** (empty-text quote post + X Article) —
    text chunking (×4 @ ≤1900) + never emitting empty components; very long tweets now render.
  * **Quoted-post rendering** (`>>> [Quote](url) from **Name** (@user)` + quoted text + quoted
    media, with full video handling on quote media too).
  * **X Article / link-card images** via OpenGraph fetch of the post's `x.com` page (article banner
    / `card_img`), falling back to the shared link's OG image (hoyo.link & co. verified working).
  * **GIF support**: `tweet_video` GIFs render as animated WebP via `gif.fxtwitter.com` when that
    CDN is up; graceful mp4 fallback when it 530s (maintainer-side).
  * **Portrait-video playback fix** via the `api.fxtwitter.com/2/go?url=…` proxy wrapper.
  * **Robust `/status/:id` API path** (the screen-name path 404s on reposts/articles/newer tweets);
    Read Post links use the true author; `/en` translation uses the same path.
  * **"↩️ Replying to"** line on replies; **animated custom emoji** on all buttons (X + Reddit).
* **2026-09-11 — round 3 (smart videos):** X V2/V3 video handling rebuilt after live Discord tests
  proved **file size** (not resolution) decides playability. Each video's real size is now probed by
  HTTP HEAD; oversized (> 256 MB) videos are swapped for a smaller playable FxTwitter `formats[]`
  rendition (905 MB 4K → 135 MB 720p that plays), or thumbnailed with a watch link when nothing
  fits. Unknown sizes are left untouched unless clearly risky (> 5 min **and** ≥ 1080p). Replaces
  the earlier pixel-count rule, which would have wrongly thumbnailed playable 2K clips.
* **2026-09-11 — round 2:**
  * **Reddit (V1 + V2):** Embeddit/vxReddit buttons removed; *Read Post* → original `reddit.com`
    permalink; YouTube link detection (bare playable link on V1, clickable line + ▶️ button on V2);
    **48-hour mod-queue-safe window** keyed on the RSS *updated* stamp so late-approved posts are
    never missed; V2 now strips HTML from **all** EmbedEZ text fields and adds a 🕐 `<t:…:f>`
    Discord timestamp to cards.
  * **X (V2 + V3):** clickable `#hashtags` / `@mentions` (masked x.com links); 🕐 Discord timestamp
    on the stats line; null-safe accent color (`accent_from_color`).
  * **Docs:** added `PRIVACY_POLICY.md` and `TERMS_OF_SERVICE.md`.
* **2026-09-11 — round 1:** Reddit V1 source-order fix (`www.reddit.com` first + feed validation +
  per-source logging); Reddit V2 rebuilt on the documented two-step EmbedEZ flow
  (`search` → `preview`) with graceful public-preview fallback.
* **Earlier:** X V1/V2/V3 engines, multi-webhook routing, `/en` auto-translation, external
  cron-job.org scheduling guide.
