# News Express — X (Twitter) + Reddit RSS → Discord Monitor (Multi-Webhook Edition)

A lightweight, **100% serverless** bot that monitors public **X (Twitter)** accounts and **subreddits**
via RSS mirrors, then posts new items to **different Discord channels** (one webhook per account/subreddit)
with rich media embeds, clickable link-style buttons, and automatic **English translation** for
non-English tweets.

No bot token. No gateway. No server. Just **GitHub Actions + Discord Webhooks**.

---

## 🌟 Credits & Acknowledgments

This project stands on the shoulders of these amazing open-source projects and free services —
please support them:

| Project / Service | What it's used for | Links |
|---|---|---|
| **News-Flash-Bot** by [@cold-logic5](https://github.com/cold-logic5) | The original repository this project is based on (RSS → Discord webhook architecture) | [GitHub repo](https://github.com/cold-logic5/News-Flash-Bot) · [Author](https://github.com/cold-logic5) |
| **Nitter** by [@zedeus](https://github.com/zedeus) | Free & open-source, privacy-focused X/Twitter front-end providing the RSS feeds | [GitHub](https://github.com/zedeus/nitter) · [status.d420.de instance tracker](https://status.d420.de/) · active fallback order reviewed 2026-09-30 (round 40): [nitter.cf](https://nitter.cf/), [xitter.cf](https://xitter.cf/), [nitter.meowing.monster](https://nitter.meowing.monster/), [nitter.netbub.com](https://nitter.netbub.com/), [shitter.thepixora.com](https://shitter.thepixora.com/), [nitter.jaydenha.uk](https://nitter.jaydenha.uk/), [nitter.miningtcup.me](https://nitter.miningtcup.me/) (RSS token) · 💖 [Donations](https://github.com/zedeus/nitter#donations) |
| **FxTwitter / FxEmbed** by [@dangered wolf](https://github.com/dangeredwolf) | Rich X/Twitter embeds (auto-unfurl) + the free API — **primary tweet-data source** (round 11; its same-engine sister client **fixupx.com** is the stand-by host) used for media, stats, translation, GIF re-rendering and the video proxy | [fxtwitter.com](https://fxtwitter.com) · [docs.fxembed.com](https://docs.fxembed.com/) · [FxEmbed GitHub](https://github.com/FxEmbed/FxEmbed) · [GitHub](https://github.com/dangeredwolf) · 💖 [Sponsor dangered wolf](https://github.com/sponsors/dangeredwolf) |
| **vxtwitter (BetterTwitFix / fixvx)** | **Backup tweet-data API** (round 11, 3rd in the fallback chain — multi-photo tweets arrive as separate photos via its API) + its **gifconvert** GIF converter (round 11) | [vxtwitter.com](https://vxtwitter.com) · [API docs](https://vxtwitter.com/api.md) |
| **EmbedEZ** | Rich Reddit embeds (redditez.com mirror) + the provider API used by Reddit V2 + **last-resort tweet-data source** behind twitterez.com (round 11) | [embedez.com](https://embedez.com/) · [redditez.com](https://embedez.com/reddit) · [twitterez.com](https://twitterez.com) · [API docs](https://embedez.com/docs) |
| **Embeddit** by [@DeltAndy123](https://github.com/DeltAndy123) | Alternative Reddit embed mirror (credited — its button was removed in the 2026-09-11 trim) | [GitHub](https://github.com/DeltAndy123/Embeddit) |
| **vxReddit** by [@dylanpdx](https://github.com/dylanpdx) | Alternative Reddit embed mirror (credited — its button was removed in the 2026-09-11 trim) | [GitHub](https://github.com/dylanpdx/vxReddit) · [vxreddit.com](https://vxreddit.com) |
| **Redlib** (community instances) | Reddit front-end mirrors used as RSS fallback sources — refreshed from the official registry on 2026-09-30; **redlib.miningtcup.me** remains the optional token-backed V3 fallback | [redlib-instances](https://github.com/redlib-org/redlib-instances) · [redlib](https://github.com/redlib-org/redlib) · [redlib.miningtcup.me](https://redlib.miningtcup.me/) (miningtcup — same operator as the nitter RSS token) |
| **Arctic Shift** by [@ArthurHeitmann](https://github.com/ArthurHeitmann) | Optional Reddit archive JSON for V3 crosspost originals, ordered galleries including GIFs, text/media fallbacks, and (round 17) the **per-subreddit search backup feed** when RSS yields no new posts. Archive availability and freshness vary; fallback counts are labelled as archived. | [GitHub](https://github.com/ArthurHeitmann/arctic_shift) · [Website](https://arctic-shift.photon-reddit.com/) · [Download tool](https://arctic-shift.photon-reddit.com/download-tool) |
| **cron-job.org** | Free external scheduler that triggers the workflows reliably every 10 minutes | [cron-job.org](https://cron-job.org) |
| **GitHub Actions** | Runs everything on a schedule, for free | — |
| **Discord Webhooks** | Delivers messages to channels statelessly | — |

Huge respect and gratitude to [@cold-logic5](https://github.com/cold-logic5) for the original
architecture, to the Nitter project — if you can, [support zedeus here](https://github.com/zedeus/nitter#donations) —
and to [@dangered wolf](https://github.com/dangeredwolf), creator and lead developer of FxTwitter/FxEmbed — donations welcome at
[github.com/sponsors/dangeredwolf](https://github.com/sponsors/dangeredwolf).

---

## ✨ Features

- 🐦 **X/Twitter monitor** with **three interchangeable render engines**:
  - **V1** — classic text + fxtwitter auto-embed, buttons below.
  - **V2** — Discord *Components V2* card (container, gallery, stats), buttons **outside** the card.
  - **V3** — same rich card, but buttons **nested inside** the container.
- 🌐 **Automatic English translation** — non-English tweets show a *"Translated from X"* block with the
  original text preserved, via FxTwitter's `/en` translation endpoint (works on V1/V2/V3).
- 📄 **Full X Articles (V2/V3, round 10)** — article tweets post their **cover image, title, full body
  text, and every in-article image/GIF** (GIFs animated via the same converter chain) straight into the
  card, from FxTwitter's article JSON — no scraping. One caveat: FxTwitter doesn't translate article
  bodies, so non-English articles post in their original language.
- 🎯 **Multi-webhook routing** — each tracked X account posts to its own Discord channel
  (`WEBHOOK_<ACCOUNT>` secrets), with an optional catch-all fallback webhook.
- 📰 **Reddit monitor** with three engines:
  - **V1** — free, no API key: posts the `redditez.com` link and lets Discord auto-embed it.
    If the thread links to YouTube, the bare YouTube URL is appended on its own line too, so a
    **playable YouTube player** appears next to the reddit embed.
  - **V2** — rich *Components V2* card built from the **EmbedEZ API** (title, media gallery, stats,
    🕐 Discord timestamp).
  - **V3 (active)** — rich *Components V2* card built from public Reddit, Redlib, and media-proxy
    fallbacks; no EmbedEZ API key is required.
- 🧵 **Round 9 (2026-09-13): one combined RSS request** — all tracked subreddits are fetched in a
  single `/r/sub1+sub2+.../new.rss` feed, which fits inside Reddit's ~1 request/minute datacenter
  rate limit; automatic per-subreddit fallback if the combined feed ever fails. Optional personal
  **`REDDIT_FEED_TOKEN`** makes it bulletproof. (See the round-9 section under the Reddit monitor.)
- 🔘 **Link-style buttons** with emoji support (Unicode **or** custom server emoji IDs). Reddit
  buttons: **Read Post → the original `reddit.com` thread**, **▶️ YouTube** (only when a link is
  detected), **Citlali News**, **Donate**.
- 🔗 **Clickable hashtags & mentions (X V2/V3)** — `#tag` → `x.com/hashtag/tag` and `@user` →
  `x.com/user` as masked links, exactly like fxtwitter auto-embeds.
- 🎬 **Smart video handling (X V2/V3)** — Discord's media gallery can't play large video files, so
  every video's **real file size is probed** (HTTP HEAD) before posting. Oversized videos are
  swapped for the biggest **smaller mp4 variant** from FxTwitter's `formats[]` that still fits
  (stays playable!), with a thumbnail + "Watch on X" link as last resort. Resolution is irrelevant —
  it's all about file size (see the live test tables below).
- 🕐 **Exact timestamps (V2/V3, X & Reddit)** — every card's stats line ends with a Discord-native
  `<t:…:f>` timestamp; hover/tap for the post's exact date & time.
- 🛡 **Mod-queue safe (Reddit)** — a 48-hour freshness window keyed on the RSS *updated* stamp means
  posts approved from a subreddit's moderator queue hours (or a day) later still get posted —
  they're never left out. Round 38e also uses the token-authenticated public RSS `/new` listing
  as the primary release signal for native zero-comment queue posts, with the existing HTML
  listing chain as a fallback and fail-open behavior preserved.
- 📊 **Stats line** — replies/retweets/likes/views (X) or comments/shares/likes/views (Reddit V2).
- 🕙 **Reliable 10-minute automation** via an external cron trigger (cron-job.org is the single
  scheduler since round 12 — the in-file GitHub `schedule:` is disabled because it raced the
  external trigger; re-enable = uncomment two lines + pause the cron-job.org job).
- 💾 **Self-maintaining memory** — posted IDs are cached in JSON files committed back to the repo by
  `github-actions[bot]`, so nothing is ever posted twice.

---

## 🗂 Repository Contents

```
├── .github/
│   ├── dependabot.yml             # Dependabot: weekly pip + actions update PRs (optional)
│   └── workflows/
│       ├── twitter_monitor.yml    # X/Twitter — runs testing area/twitter_v3.py (V3)
│       ├── reddit_monitor.yml     # Reddit (ACTIVE) — runs testing area/reddit_main_v3.py
│       ├── ci.yml                 # PR gate: install + compile + offline smoke test
│       ├── dependabot_auto_merge.yml  # opt-in auto-merge for Dependabot PRs (repo Variable)
│       └── python_version_bump.yml    # verified CPython patch/minor bump workflow
├── docs/
│   ├── REPOSITORY_TRACKING.md     # current file/config/policy inventory and audit record
│   ├── ROUND_51.md                # profile-crosspost and vxReddit shell behavior record
│   ├── ROUND_50.md                # proxy decisive-exit regression record
│   ├── ROUND_49.md                # parallel proxy dispatch and telemetry record
│   ├── ROUND_49_REPLAY_TESTS.md   # production-card replay fixture instructions
│   ├── DEPENDABOT.md              # full plain-English Dependabot explanation
│   ├── DISCOHOOK.md               # Discohook: what it's for, fully optional, safe to disable
│   ├── CI_SMOKE.md                # ci.yml + offline safety-gate explanation
│   ├── PYTHON_RUNTIME.md          # CPython pin, compatibility, performance, and update policy
│   └── other round/patch records  # historical implementation and validation notes
├── testing area/                  # tested copies of every engine (see Testing area guide)
│   ├── twitter_v1.py              # X/Twitter — V1 (plain, no API key)
│   ├── twitter_v2_button_outside.py     # X V2 (buttons outside)
│   ├── twitter_v3.py              # X V3 (buttons inside — ACTIVE)
│   ├── twitter_proxy.py           # X V3 tweet-data fallback chain (round 11: fxtwitter/fixupx/vxtwitter/twitterez)
│   ├── reddit_main.py             # Reddit V1 (free, mirror auto-embed)
│   ├── reddit_main_v2_embedez.py  # Reddit V2 (Components V2 via EmbedEZ API)
│   ├── reddit_main_v3.py          # Reddit V3 (proxy media + native fallback — ACTIVE)
│   ├── reddit_proxy.py            # Reddit V3 proxy services and health state
│   ├── reddit_signals.py          # pure Reddit gate/decision functions
│   └── video_diag.py              # X video tile diagnostic
├── tests/
│   ├── test_smoke.py              # offline smoke test (run by ci.yml on every PR)
│   ├── test_reddit_signals.py     # pure Reddit gate/unit suite
│   └── fixtures/posted_cards.py   # production-card replay fixtures
├── posted_tweets.json             # X cache (auto-committed) — start with: []
├── posted_reddit.json             # Reddit cache (auto-committed) — start with: []
├── proxy_health.json              # proxy warm-up results (auto-committed)
├── pending_reddit.json            # Reddit re-check cache (auto-committed)
├── posted_messages.json           # optional retraction state; created only when enabled
├── PRIVACY_POLICY.md              # privacy policy and state/recipient disclosure
├── TERMS_OF_SERVICE.md            # terms of service / acceptable use
├── requirements.txt               # feedparser, aiohttp, python-dotenv
├── .env.example                   # local testing template and active switches
└── .gitignore                     # ignores local/runtime state; workflows force-add caches
```

> **Engine layout note:** by default, production workflows run proven engines directly
> from their canonical paths (`testing area/twitter_v1.py`, `testing area/twitter_v3.py`,
> and `testing area/reddit_main_v3.py`). You can switch engines at any time by editing the
> workflow's `run:` line to point to the desired file (`testing area/twitter_v1.py`,
> `testing area/twitter_v2_button_outside.py`, `testing area/twitter_v3.py`,
> `testing area/reddit_main.py`, `testing area/reddit_main_v2_embedez.py`, or
> `testing area/reddit_main_v3.py`).

---

## 🧪 Testing area — how updates are tested before going live

Every new or changed script is proven **before** it touches production. The process:

1. **The updated script lives in the `testing area/` folder first** (e.g. `testing area/reddit_main_v3.py`,
   `testing area/twitter_v3.py`). Never run an unproven script from the repo root.
2. **Point the workflow's `run:` line at the test copy.** The **double quotes are required** because
   the folder name contains a space:
   ```yaml
   run: python "testing area/reddit_main_v3.py"
   ```
3. **Check two things:**
   - the actual post(s) in Discord (layout, buttons, media), **and**
   - the workflow log (Actions tab) — every skipped source/instance is logged there.
4. **Once both look right, point the workflow's `run:` line to your preferred active engine:**
   - For X/Twitter: `"testing area/twitter_v1.py"`, `"testing area/twitter_v2_button_outside.py"`, or `"testing area/twitter_v3.py"`
   - For Reddit: `"testing area/reddit_main.py"`, `"testing area/reddit_main_v2_embedez.py"`, or `"testing area/reddit_main_v3.py"`
5. Commit. Production is updated; the test file can stay or be deleted.

> The same guidance is written as a comment block inside both workflow yml files, right above the
> `run:` line, so future readers find it there too.

---

# 🐦 X (Twitter) Monitor

## Choosing a version (V1 vs V2 vs V3)

All three do the same job with the same multi-webhook routing and translation — they only differ in
**how the Discord message looks**:

| | `twitter_v1.py` (V1) | `twitter_v2_button_outside.py` (V2) | `twitter_v3.py` (V3 — **current**) |
|---|---|---|---|
| Message style | Plain text + fxtwitter link → Discord **auto-unfurls** the embed | Fully custom **Components V2** bordered card (type 17 container + text + media gallery + stats) | Same custom card as V2 |
| Buttons | Action row below the embed | Action row **outside/below** the container | Action row **nested inside** the container |
| Data source | RSS + FxTwitter API (light, lang check only) | RSS + FxTwitter API (full tweet JSON) | RSS + FxTwitter API (full tweet JSON) |
| Custom accent color | n/a | ✅ (per-tweet `color`) | ✅ (per-tweet `color`) |
| Switch to it | `run: python "testing area/twitter_v1.py"` | `run: python "testing area/twitter_v2_button_outside.py"` | `run: python "testing area/twitter_v3.py"` |

**To switch versions:** open `.github/workflows/twitter_monitor.yml` and change the run line:

```yaml
# run: python "testing area/twitter_v1.py"               # V1
# run: python "testing area/twitter_v2_button_outside.py" # V2
run: python "testing area/twitter_v3.py"                 # V3 (active)
```

Commit — done. All three were verified working end-to-end (feeds, translation, per-channel routing,
buttons, and cache commits).

## 🆕 X V2/V3 card behaviors (2026-09-11 update)

* **Clickable hashtags & mentions** — `#tag` → `[#tag](https://x.com/hashtag/tag)`, `@user` →
  `[@user](https://x.com/user)`; bare http(s) links are auto-linked by Discord as before.
  Regex lookbehinds protect URLs like `example.com/path#anchor` and emails like `a@b.com` from being
  linkified by accident.
* **Smart video handling (revised after live testing).** Your tests proved the breakage is about
  **file size, not resolution**:

  | Video | Real size (probed) | Components V2 gallery |
  |---|---|---|
  | 3840×2160 · 24 min | 905 MB | ❌ "image failed to load" |
  | 1920×1080 · 56 min | 578 MB | ⚠️ loads, won't play |
  | 2560×1440 · 5:12 | 405 MB | ❌ "image failed to load" |
  | 2560×1440 · 1:28 | 120 MB | ✅ plays |
  | 3440×1440 · 0:24 | 22 MB | ✅ plays |
  | 2340×1080 · 4:29 | 191 MB | ✅ plays |

  So the scripts now **probe every video's real file size** with an HTTP HEAD request
  (`Content-Length`, with a Range-GET backup) and apply these rules — nothing is forced when the
  size can't be determined:
  * **≤ 256 MB** (`VIDEO_SIZE_LIMIT`, tunable) → video goes in the gallery as-is (confirmed safe zone:
    191 MB works, 405 MB fails).
  * **Over the limit** → the script tries FxTwitter's `formats[]` list (smaller mp4 renditions,
    highest quality first) and probes each; the first that fits is embedded instead, with a
    `🔽 Original video is ~X MB — showing a smaller version (~Y MB)… ▶️ Watch full quality on X`
    note. Example live result: the 905 MB 4K Wuthering video → 1280×720 variant (~135 MB) that
    **plays in Discord**.
  * **Over the limit + no fitting variant** → the video's **thumbnail** appears in the gallery plus
    a `⚠️ Video is ~X MB — ▶️ Watch it on X` note (covers the 56-minute Genshin case).
  * **Size undetectable** → the video is left untouched (never forced) **unless** it's clearly
    risky (> 5 minutes *and* ≥ 1080p — matches every verified failure), in which case it's
    thumbnailed with a watch link. A 2K clip of 1:28 stays in the gallery.
* **Discord timestamp** — the stats line ends with `🕐 <t:epoch:f>` (taken from FxTwitter's
  `created_timestamp`, falling back to `created_at`, then the RSS publish date).
* **Null-safe accent color** — FxTwitter sometimes returns `"color": null`; the card now falls back
  to Twitter blue instead of crashing.

## 🆕 X V2/V3 card behaviors — round 4 (2026-09-11)

Fixes and formats added after real feed runs:

* **Discord `400 {"components": ["0"]}` errors — FIXED.** Root cause: tweets with an **empty body**
  (a repost of a media-only quote post; an X Article) produced a zero-length text component, which
  Discord rejects. Text is now chunked (≤ 1900 chars per component, up to 4 components) and empty
  components are never emitted — so **very long tweets also render now** instead of failing.
* **Quoted posts are rendered.** Tweets quoting another post show:
  `>>> [Quote](url) from **Name** (@user)` + the quoted text + the quoted tweet's own media gallery
  (videos in quotes get the same size/GIF/portrait treatment).
* **X Articles & link cards get their image.** When a tweet has no media, the script fetches the
  tweet's own `x.com` page and reads its OpenGraph image — for X Articles that's the **article
  banner**, for link posts (e.g. `hoyo.link`) it's the **card image**. Fallback: the first external
  link's `og:image` (works for hoyoverse/kurogames pages). Profile pictures are never used, and the
  extra fetch is skipped for normal tweets. (Round 10 supersedes this for articles — see below: the
  full article now renders, not just its banner.)
* **GIF support.** X "GIFs" are internally tiny looping mp4s (`tweet_video/*.mp4`). When detected,
  the script swaps in a real **animated image** so it plays inline instead of sitting in a video
  player. Two community converters are probed in order — **never forced**:
  1. FxTwitter's official animated WebP (`gif.fxtwitter.com/tweet_video/*.webp`) — the same asset
     V1 embeds use. Its CDN is **intermittently down** (Cloudflare 530/1033, confirmed live).
  2. **fastgif** (`fastgif-production.up.railway.app/tweet_video/*.gif`) — an independent
     third-party converter that outputs true GIFs (round 6). Only its `.gif` route works (its
     `.webp` route errors), and unknown ids return 500, which makes it safely probeable.

  Each source is HEAD-probed before use; if the first is down the second takes over automatically,
  and if neither answers, the mp4 is kept, which still plays as a video. The chain is self-healing
  in both directions — the moment `gif.fxtwitter.com` recovers it becomes the primary again.
* **Portrait videos that "load but won't play" — root-caused in round 5.** Vertical videos
  (`h > w`, e.g. the 58s Jingran showcase) intermittently failed to play right after posting —
  but follow-up tests showed the **same direct URLs playing fine** in Components V2 shortly after
  (even media that had failed earlier). It was a transient Discord proxy warm-up issue, not a
  portrait incompatibility, so direct URLs are now used for all videos (same as every other embed
  service). A documented one-line toggle (`PORTRAIT_PROXY = True`) can re-route vertical videos
  through FxTwitter's embed proxy (`/2/go?url=…`) if genuine breakage is ever proven again.
* **`/status/:id` API path.** The screen-name API path (`/<user>/status/:id`) returns **404** for
  reposts of other authors, X Articles, and some newer tweets (verified live); the plain-ID path
  resolves everything. Read Post links now use the **true author** from the payload, so reposts link
  to the original post correctly. Same for the `/en` translation fetch.
* **"↩️ Replying to @user"** small line appears on replies (links to the parent post when known).
* **New animated button emoji** on X *and* Reddit (per your spec): Read Post
  `<a:starwardhmm:1472388018689282261>`, Citlali News `<a:starward11:1439878792653832253>`, Donate
  `<a:starwardfans:1509026327548657914>`.
* **Interactive campaign tweets** (multi-photo, e.g. the "mysterious manuscript" Wuthering post) —
  all 4 photos render in the gallery; verified against the live API.

## 🆕 X V2/V3 card behaviors — round 10 (2026-09-13)

* **Full X Article support (verified live).** FxTwitter's API returns each article as clean JSON
  (`tweet.article`: title, cover image, draft.js text blocks, in-article media) — no x.com scraping,
  no login. Article tweets now post as: **cover image** (right under the header) → **title** + full
  body text (chunked exactly like tweets) → **in-article media gallery** (images as-is; in-article
  GIFs go through the same animated `gif.fxtwitter` → `fastgif` chain; in-article videos get the
  same size probe / downgrade handling) → stats → buttons. The round-4 "banner only" OpenGraph
  behavior no longer applies to articles — they render fully.
  * Note: FxTwitter does **not** translate article bodies (there is no `/en` for them), so
    non-English articles post in their original language. Normal tweets still get `/en`.
  * Verified live 2026-09-13: HonkaiNA "DevTalk | Evolution Test Wrap-Up" posted as cover + title +
    text + 4-item gallery (3 images + 1 animated GIF); log line
    `V3 Posted: HonkaiNA_2081590638282432606 (lang=en | article)`.
* **Video gallery limit — live re-verified with a full diagnostic.** A one-off diagnostic card
  (`testing area/video_diag.py`) posted labeled test tiles at every size and URL style to a channel;
  results 2026-09-13:

  | Tile | Result |
  |---|---|
  | 19.3 MB / 10.6 MB (270p) | ✅ plays — all URL styles |
  | **170.8 MB (720p)** — what the bot embeds | ✅ plays — all URL styles |
  | **233.8 MB (1080p)** — what the bot embeds | ✅ plays — all URL styles |
  | 521.7 MB (1080p) | ❌ "image not found" — every style |
  | 824 MB / 1782 MB (4K) | ❌ "image not found" — every style |

  So the 256 MB `VIDEO_SIZE_LIMIT` sits in a **proven-safe gap** (≤ 234 MB plays; ≥ 521 MB never
  gets sent because the downgrade rule swaps first) — no default changed. The test also proved the
  `?tag=` query parameter and the fxtwitter proxy origin are **irrelevant** to playability — the
  plain direct URLs are what play.
* **`GALLERY_VIDEO_LIMIT` (new constant, default `0` = off, behaviour unchanged).** An optional
  extra safety cap for the gallery: if Discord's proxy ever breaks a ≤ 256 MB tile again, set it to
  the largest size that proved playable (e.g. `GALLERY_VIDEO_LIMIT = 100 * 1024 * 1024`) — videos
  above it then auto-downgrade to the largest variant at/below it (checking **all** variants, not
  just the top 3), or post a "watch on X" note, so the gallery can never carry a tile Discord's
  proxy can't play.
* **"image not found" on an already-posted video — what to do.** Discord's media proxy fetches each
  tile's URL **once**, when the message is created. If that single fetch hiccups (transient proxy
  warm-up / CDN edge — the same class of event as the round-5 portrait case), the tile shows
  "image not found" **for that message forever**: reloading Discord doesn't fix it, but
  **re-posting the same URL works** (verified twice, 2026-09-13). The bot can't detect the failure
  itself (the webhook answers "OK" before the proxy fetch even starts — no API exposes tile
  status), so the recovery stays a 30-second manual fix:
  1. Delete the broken message in Discord.
  2. Remove that tweet's line (e.g. `"Ananta_EN_1970307131074355593"`) from `posted_tweets.json`.
  3. Re-run the workflow (or just wait for the next 10-minute run).

  As of 2026-09-13 this had happened exactly once (2 tiles out of hundreds of posts).

## 🆕 X V2/V3 card behaviors — round 11 (2026-09-17): tweet-data fallback chain + GIF restructure

* **Tweet data now has a 4-step fallback chain** (new module `testing
  area/twitter_proxy.py` — the same "mix of services" idea as the Reddit
  proxies, all keyless). The **main source is FxEmbed's FxTwitter API**
  (`api.fxtwitter.com`, docs.fxembed.com); if it can't answer, the chain
  continues seamlessly:
  1. **fxtwitter** — primary (full features: media, quotes, X Articles,
     `/en` translation, views).
  2. **fixupx** (`api.fixupx.com`) — FxEmbed's sister client: **same engine,
     same creator, same domain family** as fxtwitter.com — a hot stand-by on
     a different host. Not listed in the public FxEmbed API docs, so if that
     host doesn't resolve the step fails in ~0 ms and the chain continues —
     safe either way.
  3. **vxtwitter** (`api.vxtwitter.com` — BetterTwitFix, the site behind
     vxtwitter.com/fixvx): text, media, quoted tweets, lang, epoch date,
     stats. **Multi-photo tweets arrive as one entry per photo** (verified
     live 2026-09-17 — its combined-grid image is a website-only
     presentation field and is ignored). No view counts, no X Article
     bodies.
  4. **twitterez** (the EmbedEZ backend behind twitterez.com — the same
     engine redditez.com uses for Reddit): keyless search API → stable key →
     bot embed page og: tags. Media arrives as embedez redirect URLs (GIFs
     as animated `.webp` that Discord loops natively), text + stats line
     (`💬/🔁/💜/👀`, compact numbers incl. `1.5M`). Its occasional promo line
     ("Add the EmbedEZ bot… (ad)") is stripped, and a video tweet's poster
     frame is not duplicated as a photo.
  **Seamless by design:** every service's result is normalized to the exact
  FxTwitter `tweet` shape *before* the card pipeline runs, so layout, media,
  stats, quotes, GIF handling and buttons are identical no matter who
  answered. The winner is logged per tweet —
  `V3 Posted: … (… | source=vxtwitter)` — and a fallback also logs
  `tweet data via vxtwitter (fallback).` If the module file is ever
  missing, the script logs a warning and runs the legacy direct FxTwitter
  call — nothing breaks. `/en` translation is attempted only when the data
  came from FxTwitter itself.
* **GIF converter chain restructured** (fastgif went offline 2026-09-17).
  Probed in order, never forced:
  1. `gif.fxtwitter.com/tweet_video/*.webp` — FxTwitter's official animated
     WebP (intermittent Cloudflare 530s, so probe-gated).
  2. `gifconvert.vxtwitter.com/convert.webp?url=<mp4>` — BetterTwitFix's
     converter (the exact URL shape vxtwitter's own embeds use — verified
     live; they use `.avif`, which Discord's gallery can't render, so we
     probe `.webp` first). Header-gated: probed with a browser Referer.
  3. `gifconvert.vxtwitter.com/convert.gif?url=<mp4>`
  4. `fastgif-production.up.railway.app/tweet_video/*.gif` — **offline since
     2026-09-17** (404 on every route); kept as the *last* probe so it is
     used automatically again if it ever comes back.
  If nothing answers, the mp4 is kept (plays as a video) — unchanged.
* **Reddit V3 got its matching backup the same round** — see the round-17
  section under the Reddit monitor.

## 🆕 X V2/V3 — round 12 (2026-09-17): nitter fleet resilience + visible failures + TEST_TWEET_ID

**What broke:** on 2026-09-17 every nitter instance the monitor knew about
was dead or stale (nitter.net / nitter.privacydev.net returned HTTP 500,
xcancel.com was suspended 2026-09-14, nitter.perennialte.ch served a stale
feed) — and the old `fetch_working_feed` logged **nothing** on that path, so
the monitor silently no-oped and missed tweets (e.g.
`Wuthering_Waves/2100555373073797461`, the EP3.7 song-credit post) with zero
log lines to explain why.

**What round 12 does:**

1. **Every feed attempt is logged** — per instance: `feed OK via … — N
   entries`, `HTTP 500 — trying next`, `HTTP 200 but 0 entries (bot check /
   stale instance?) — trying next`, or the exception name; if no instance
   works: `NO working nitter instance this run — account skipped`; if no
   account gets a feed at all: `ALL FEEDS FAILED this run` (ERROR level). A
   dead fleet can never be invisible again.
2. **The RSS fleet now covers the WHOLE tracked fleet — 11 instances**
   (status.d420.de tracker + live plain-RSS probes, 2026-09-17), ordered by
   today's evidence because the tracker's health/RSS flags flip back and
   forth from day to day: `jaydenha.uk` + `meowing.monster` (both verified
   fresh by probe) → `click` / `xitter.cc` (RSS "disabled" at probe time —
   kept, flags flip) → `miningtcup.me` (healthy, RSS **token-gated** — see
   3.) → `netbub` (unreachable) → `thepixora` (alive, behind a dog-captcha
   bot check) → `perennialte.ch` (stale RSS) → `privacydev.net` /
   `nitter.net` (500'd) → `xcancel.com` (suspended — kept: auto-revives in
   the chain if it returns). The chain stops at the first instance that
   answers with real entries, so a dead one in the list costs at most a
   logged line.
3. **RSS token support for `nitter.miningtcup.me`** (bot check). A token
   request was emailed to `nitter-rss@miningtcup.me`. **When the token
   arrives:**
   * **Repo → Settings → Secrets and variables → Actions → Secrets →
     New repository secret** → name **`NITTER_RSS_TOKEN`**, value = the
     token from the email. (A repo *secret*, not a *variable* — GitHub
     masks secrets in every log line; variables print in plain text,
     which is how the token ended up visible in the run logs.)
   * That's it. The workflow already wires
     `NITTER_RSS_TOKEN: ${{ secrets.NITTER_RSS_TOKEN }}` and the script
     reads it at call time — the **next cron-job.org run** picks it up
     automatically (no code change, no re-deploy). The token is sent BOTH as
     an `Authorization: Bearer` header and a `?token=` query param, so
     either token convention the instance uses works. Until then the chain
     simply logs the bot-check answer for that instance and moves on.
4. **`TEST_TWEET_ID` recovery net** — the workflow's *Run workflow* panel has
   an optional **test_tweet** input. Fill it with `screen_name/tweet_id`
   (a full x.com status URL also works) to rebuild ONE specific tweet
   through the same pipeline + cache, bypassing nitter entirely (FxTwitter
   direct). Example: `Wuthering_Waves/2100555373073797461`. Already-posted
   tweets are skipped by the cache, so it's safe to re-run.
5. **GitHub's native `schedule:` is now disabled** in BOTH monitor
   workflows (commented out with a re-enable note). cron-job.org is the
   single scheduler — the native schedule had raced it (2026-09-17
   `WutheringWavesLeaks_1wis2u5` double post: both checked out the same
   pre-cache commit, both posted, the 2nd cache push was rejected). To
   re-enable: uncomment the two `schedule:` lines AND pause the cron-job.org
   job.

**Catch-up:** with the fleet refreshed, the next cron-job.org run
automatically posts the missed 2026-09-17 tweets (WW song credits + video,
the 08:00 wallpaper, the TYPEII_EN repost of @zeroartwo, and the Ananta_EN
11:37 giveaway-winner announcement) — no manual action needed.

## 🆕 X V2/V3 — round 13 (2026-09-17): repost attribution

When a tracked account **reposts** (retweets) someone else's tweet, the card
now says who did the reposting instead of presenting it as the original
author's own tweet:

* **Header:** `### [TYPEII_EN reposted](https://x.com/TYPEII_EN)` — the
  reposting account (screen name, per 2026-09-17) linking to its profile.
* **Original line under the header:** `-# 📌 Original: [円 (@zeroartwo)](https://x.com/zeroartwo)`
  so the true author stays visible.
* Everything else is unchanged: the *Read Post* button still opens the
  original tweet, stats/timestamp are the original's, translation and media
  work exactly as before.

**How it's detected (no new API needed):** a nitter feed for an account
contains only that account's own tweets and its reposts — so when the true
author returned by the tweet-data API differs from the feed account, the
entry is a repost by the feed account. (FxEmbed's payload does include a
`reposted_by` field, but it is only set when the RETWEET's own status id is
queried; nitter RSS links point at the original author's status, so the feed
itself is the signal.)

## 🆕 X V2/V3 — round 14 (2026-09-18): miningtcup RSS token live (sent two ways)

The emailed RSS token for the token-gated `nitter.miningtcup.me` instance
is now sent in **BOTH** places its operator (`nitter-rss@miningtcup.me`)
confirmed it is accepted — the `Authorization: Bearer` header **and**
inside the `User-Agent` (the round-12 `?token=` query param is kept, so
all three conventions are covered at once):

```python
req_headers = {**headers,
               "Authorization": f"Bearer {token}",
               "User-Agent": f"Mozilla/5.0 {token}"}
feed_url = f"{feed_url}?token={url_quote(token, safe='')}"
```

* **One-time setup:** put the token in the existing repo secret
  `NITTER_RSS_TOKEN` (Settings → Secrets and variables → Actions →
  Secrets). Nothing else to do — the next cron-job.org run picks it up.
* **Effect:** `miningtcup.me` (the one token-gated instance of the
  11-instance fleet) joins the chain as a normal instance instead of
  logging a bot-check miss. If it ever answers with 0 entries, it is
  logged and the chain moves on, exactly as in round 12.
* **Credits:** token-gated RSS instance + token provided by
  **miningtcup** (`nitter.miningtcup.me`) — thank you!

## 🌐 How translation works (all versions)

1. The script fetches the tweet from the FxTwitter API and reads its `lang` field.
   (Round 11: the tweet data may instead come from a backup service in the
   fallback chain — see the round-11 section; the `/en` re-fetch below is
   attempted only when the data came from FxTwitter itself.)
2. If it's not English, it re-fetches the tweet with `/en`, which returns the
   translation inside a separate `translation` object (`text`, `source_lang`,
   …) — the original `text`/`lang` fields are left untouched.
3. The message shows **🌐 Translated from {Language}** then the translation, then an
   **Original text** block with the untranslated tweet. The *Read Post* button points to the `/en`
   fxtwitter page too.
4. Round 28 (2026-09-18): X's per-tweet `lang` is an automatic guess and
   misfires on short/ambiguous text (live case: "Maintenance 🩸" + hashtags,
   tagged `fr` by an ESP/ENG artist). When the `/en` translation comes back
   IDENTICAL to the original text, the block is dropped and the card posts
   as-is (logged as "X language mis-detection"); a real translation always
   differs, so legitimate "Translated from …" cards are unaffected.
5. If FxTwitter can't translate a specific post, the script gracefully posts the original text instead.
6. `LANGUAGE_NAMES` at the top of each file maps ISO codes (ja, ko, zh, fr, …) to readable names —
   extend it if you track accounts in other languages. (V1 note: V1 posts the
   fxtwitter auto-embed of the original tweet and doesn't do its own `/en`
   re-fetch, so the guard above only applies to the V2/V3 card engines.)

## 🎯 Multi-webhook routing

Every account in `ACCOUNTS` is routed to its own webhook secret:

| Setting | Example |
|---|---|
| `ACCOUNTS` secret | `TYPEII_EN,PomPom_HonkaiSR,Wuthering_Waves,HonkaiNA,Ananta_EN` |
| Per-account secret name | `WEBHOOK_` + account name **UPPERCASED**, non-alphanumerics → `_` |
| `TYPEII_EN` → | `WEBHOOK_TYPEII_EN` (e.g. `#zzz-news`) |
| `PomPom_HonkaiSR` → | `WEBHOOK_POMPOM_HONKAISR` (e.g. `#hsr-news`) |
| `Wuthering_Waves` → | `WEBHOOK_WUTHERING_WAVES` (e.g. `#wuwa-news`) |
| `HonkaiNA` → | `WEBHOOK_HONKAINA` |
| `Ananta_EN` → | `WEBHOOK_ANANTA_EN` (e.g. `#ananta-news`) |
| fallback (optional) | `DISCORD_WEBHOOK_URL` — used for any account without its own secret |

### The workflow (`.github/workflows/twitter_monitor.yml`)

```yaml
name: Twitter Feed Monitor

on:
  # ── GITHUB NATIVE SCHEDULE: DISABLED (round 12, 2026-09-17) ────────────────
  # It raced the cron-job.org trigger (double post, 2026-09-17). To re-enable:
  # uncomment these two lines AND pause the cron-job.org job:
  #   schedule:
  #     - cron: '*/10 * * * *'
  workflow_dispatch:          # allows manual + external-cron triggering
    inputs:
      test_tweet:
        description: 'Optional: rebuild ONE specific tweet, e.g. Wuthering_Waves/2100555373073797461 (nitter bypassed). Leave empty for a normal run.'
        required: false
        default: ''

permissions:
  contents: write

jobs:
  check-rss:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: '3.14.7'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Twitter Feed Monitor
        env:
          ACCOUNTS: ${{ secrets.ACCOUNTS }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          WEBHOOK_TYPEII_EN: ${{ secrets.WEBHOOK_TYPEII_EN }}
          WEBHOOK_POMPOM_HONKAISR: ${{ secrets.WEBHOOK_POMPOM_HONKAISR }}
          WEBHOOK_WUTHERING_WAVES: ${{ secrets.WEBHOOK_WUTHERING_WAVES }}
          WEBHOOK_HONKAINA: ${{ secrets.WEBHOOK_HONKAINA }}
          WEBHOOK_ANANTA_EN: ${{ secrets.WEBHOOK_ANANTA_EN }}
          # Test tools (round 12): TEST_TWEET_ID rebuilds one tweet nitter-free
          # (manual runs only); NITTER_RSS_TOKEN feeds the token-gated
          # nitter.miningtcup.me instance (repo SECRET — GitHub masks
          # secret values in all logs automatically).
          TEST_TWEET_ID: ${{ github.event.inputs.test_tweet }}
          NITTER_RSS_TOKEN: ${{ secrets.NITTER_RSS_TOKEN }}
        # While testing a new version, point this line at the test copy instead
        # (QUOTES REQUIRED — the folder name has a space):
        #   run: python "testing area/twitter_v3.py"
        run: python "testing area/twitter_v3.py"   # ← switch to testing area/twitter_v1.py / twitter_v2_button_outside.py here

      - name: Persist updated posted_tweets.json cache (retry safely on a concurrent main update)
        env:
          CACHE_BRANCH: ${{ github.ref_name }}
        run: |
          set -o pipefail
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add -f posted_tweets.json

          if git diff --cached --quiet; then
            echo "No cache changes to push."
          else
            if ! git commit -m "auto: update posted_tweets.json cache"; then
              echo "::error::CACHE COMMIT FAILED — dedup cache was not persisted; rerun this monitor after resolving the repository state."
              exit 1
            fi

            cache_branch="${CACHE_BRANCH:-main}"
            pushed=0
            attempts=0
            for attempt in 1 2 3; do
              attempts="$attempt"
              if git push origin "HEAD:${cache_branch}"; then
                pushed=1
                break
              fi

              # A remote cache commit may have landed between checkout and push.
              # Rebase our single cache commit, then retry with bounded backoff.
              if [ "$attempt" -lt 3 ]; then
                echo "::warning::Cache push attempt $attempt/3 failed; rebasing ${cache_branch} before retry."
                if ! git pull --rebase origin "$cache_branch"; then
                  git rebase --abort || true
                  echo "::error::CACHE PUSH RECOVERY FAILED — rebase could not complete; dedup cache was not persisted."
                  break
                fi
                sleep "$((attempt * 15))"
              fi
            done

            if [ "$pushed" -ne 1 ]; then
              echo "::error::CACHE PUSH FAILED after ${attempts}/3 attempt(s) — dedup cache was not persisted; the next run may re-post. Rerun this monitor after GitHub recovers."
              exit 1
            fi
          fi

```

> Every webhook secret you add must get a matching `WEBHOOK_...` line in the `env:` block —
> that's the one manual step when adding a new account.

## 🔘 Customizing the buttons (all files)

Near the top of each script:

```python
READ_POST_LABEL = "Read Post"
READ_POST_EMOJI = {"name": "📖"}        # Unicode emoji — or None
STATIC_BUTTONS = [
    {"label": "Citlali News", "url": "https://discord.gg/HyrVP9wRXu", "emoji": {"name": "✨"}},
    {"label": "Donate",     "url": "https://ko-fi.com/jieunlatte",   "emoji": {"name": "☕"}},
]
```

* Max **5 buttons per row** (Discord limit).
* **Custom server emoji:** type `\:emojiname:` in Discord to get its ID, then use:
  `"emoji": {"id": "123456789012345678", "name": "emojiname", "animated": False}`
  (`animated: True` for GIF emoji). Full custom *pictures* on buttons are not possible — Discord only
  supports label + one emoji.

---

# 📰 Reddit Monitor

Monitors subreddits through RSS (sorted by *new*) and posts each new thread to that subreddit's own
Discord channel.

## Choosing a version (V1 vs V2 vs V3)

| | `reddit_main.py` (V1) | `reddit_main_v2_embedez.py` (V2) | `reddit_main_v3.py` (V3 — **current**) |
|---|---|---|---|
| Cost | **Free — no API key at all** | Requires an **EmbedEZ API key** (paid credits — see concerns below) | **Free — no API key at all** (Reddit's own media URLs) |
| Look | Plain message + `redditez.com` link → Discord auto-embeds it (same idea as fxtwitter), plus a bare YouTube link with its own playable embed when detected | Rich **Components V2** card built from EmbedEZ data | Same rich **Components V2** card, built from **Reddit's own URLs** |
| Media | Whatever the mirror unfurls | Up to 10 media items via EmbedEZ | **Every photo** (up to 20 → 2 containers), best rendition per photo (full-res `i.redd.it` for jpgs); video posts show the **video only**; never a silent video |
| YouTube | Bare link (auto-embeds) + conditional button | Clickable line + button | **Thumbnail + animated `starwardspark3` button** (deterministic); optional real playback via `YOUTUBE_MEDIA_EMBED=1` |
| Extra | — | — | 💬/👍 stats + **💬 OP comment** (FULL MODE), true crosspost embeds (fetches the original post), native `v.redd.it` video chain, **Discohook preview link** logged per card |
| Switch to it | `run: python "testing area/reddit_main.py"` | `run: python "testing area/reddit_main_v2_embedez.py"` | `run: python "testing area/reddit_main_v3.py"` |

### 🆕 Reddit V3 — what's different (round 12, 2026-09-15)

* **All photos, always.** Multi-image posts post every photo.
  Single-image posts: the RSS content is scanned for every `redd.it` media
  URL in post order (instead of only the feed's single 140px thumbnail).
  Multi-image GALLERY posts (whose RSS content carries **no** image links —
  verified in the 2026-09-15 workflow log) get a best-effort post-page
  harvest from the redlib fallback instances, probed in parallel (~10s worst
  case; if every instance fails, the single-thumbnail card is kept —
  FULL MODE with an OAuth app is the definitive gallery source). Renditions:
  `i.redd.it` full-res swap for jpg/jpeg, largest signed preview URL for
  PNGs — the 140px feed thumb is no longer used.
* **Clean body text.** Stray `redd.it` image URLs that used to linger in the
  body are stripped (they belong in the media gallery).
* **Video = video only.** Posts with a reddit video (or a YouTube link) show
  the video tile only — the duplicate first-frame / `external-preview.redd.it`
  screenshot is dropped.
* **Native video chain (no key, no proxy first).** `fallback_url` (FULL MODE)
  → `v.redd.it/<id>/DASH_<q>.mp4` (self-contained mp4 **with audio**, straight
  from Reddit, no signature, no expiry — tried 720→1080→480→360) → the
  embedez/vxreddit CMAF muxing proxies as last resort. The signed
  `packaged-media.redd.it` DASH master links are **not** used (they expire in
  hours — the `e=…` param).
* **YouTube (default: thumb + button).** The `YOUTUBE_MEDIA_EMBED` playback
  attempt (seaof.glass) is **off by default** — it adds up to ~3 min of
  per-post probe time and third-party flakiness. Default behavior: best
  available `i.ytimg.com` thumbnail in the gallery + the animated
  `starwardspark3` **YouTube** button. Set `YOUTUBE_MEDIA_EMBED=1` to re-enable
  playback attempts (still degrades to thumb+button automatically).
* **💬 OP comment (FULL MODE).** The stickied/top top-level comment by the
  post author is fetched with the post JSON and shown as a capped (500 char)
  line with a *full comment* link. `REDDIT_OP_COMMENT=0` disables.
* **4000-char budget.** Header + body + OP line + stats are budgeted so the
  card never exceeds Discord's total text limit (body is auto-trimmed last).
* **Discohook preview.** After each successful post, a keyless public share
  link rendering the exact card is created and logged (see
  [Discohook](#-discohook-integration-round-12) below). `DISCOHOOK_PREVIEW=0`
  disables.
* **Test tools (verify before promoting).** In the V3 workflow
  (`workflow_dispatch`):
  * **`test_post`** input = `<subreddit>/<post_id>` (e.g. `AnantaLeaks/1wgvcz7`)
    rebuilds exactly that post (bypasses feed + dedup). Data source: the post
    JSON when reachable (FULL MODE); otherwise the post's RSS feed entry
    (100-entry window) or a redlib post page (round 12c — works in native
    mode too).
  * **`dry_run: yes`** builds + logs the full payloads **without** posting to
    Discord or saving the cache. Use both together to re-test the exact posts
    that were wrong without spammng the channel.
* **Environment switches** (all optional — sane defaults without them):
  `YOUTUBE_MEDIA_EMBED` (default off), `REDDIT_OP_COMMENT` (default on),
  `DISCOHOOK_PREVIEW` (default on), `FEEDTOKEN_JSON_STAGGER` (default 65 s),
  `REDDIT_JSON_PROBE` (default `auto`), `PROXY_MEDIA` (default on),
  `PROXY_WARMUP_POST`, `EMBEDDIT_INSTANCE`, `YOUTUBE_LINK_MESSAGE` (default
  on), `PENDING_RECHECK_SECONDS` (default 1800 s), and the round-42–50 gate,
  listing, and proxy timing switches shown in [`.env.example`](.env.example).
  That template is the source of truth for the complete local switch list and
  its matching GitHub Actions repository Variables.

### 🆕 Reddit V3 — round 13 (2026-09-16): proxy media services

Native-mode card media now comes from the **public proxy services** before
falling back to RSS — same services you tested by hand (all keyless, no
credits, no API key):

| Priority | Service | What the bot reads from it | Video audio |
|---|---|---|---|
| 1 | **redditez.com** (EmbedEZ) | keyless `search` API → stable key → bot embed page og: tags (photos as embedez media URLs, title/body/stats) | ✅ (playable mp4) |
| 2 | **vxreddit.com** | bot embed page og: tags — every gallery photo as **full-res `i.redd.it`**, stats in `og:site_name` | ✅ (muxed `redditvideo.mp4`) |
| 3 | **embeddit.deltandy.me** | Mastodon-style JSON API — **ALL gallery photos (20)**, body, stats, author | ✅ under ~50 MB (merged mp4) |

* **Fallback chain (your spec):** redditez first; if it's down, or if its
  page shows *"Failed to Get Post | EmbedEZ — Reddit returned a non-JSON
  response"* (that message means the EmbedEZ backend behind redditez —
  which fetches the post from Reddit for us — is down or unavailable at
  that moment; a service-side failure, not a problem with the post), the
  post falls through to **vxreddit**, then **embeddit** — the two most
  uptime-reliable. Detected per post, not just at warm-up. Their own
  URLs are mixed into the components-v2 card verbatim (Discord fetches each
  media URL itself).
* **Warm-up link test (your spec):** every run first probes all three with
  one known post (default `HonkaiStarRail_leaks/1whbjbh`, override
  `PROXY_WARMUP_POST`) and writes **`proxy_health.json`** (auto-committed).
  Dead services are skipped for the run; if ALL three are dead, every
  service is retried per post. Log lines: `[proxy warm-up] <service>: OK/DOWN`.
* **Then the old native path:** if no service can serve a post, the round-12
  RSS media path runs unchanged (RSS media → redlib harvest → thumbnail).
  `PROXY_MEDIA=0` disables the proxy path entirely. **FULL MODE** (OAuth
  app) and test posts are unaffected — proxies also make any-age test posts
  work when the post JSON 403s.
* **Videos are range-checked** before use (muxed mp4 with audio); if the
  proxy video URL dies, the native `v.redd.it` DASH chain (with audio) runs
  instead. Video posts still show **video only** (no duplicate poster).
* **20-photo galleries = 2 containers** (10 media items each) — unchanged;
  **crossposts** keep working (the proxy returns the crosspost's own
  content; FULL MODE still fetches the original post).
* **YouTube second message (your spec):** after the card lands, the bot
  posts a **second plain message containing only the YouTube link** (Discord
  shows the official preview — no buttons, nothing else). The card's own
  YouTube thumbnail + animated `starwardspark3` button stay.
  `YOUTUBE_LINK_MESSAGE=0` disables the second message.
* **New switches** (repo Variables, all optional): `PROXY_MEDIA` (on),
  `PROXY_WARMUP_POST` (`HonkaiStarRail_leaks/1whbjbh`),
  `YOUTUBE_LINK_MESSAGE` (on), `EMBEDDIT_INSTANCE` (self-hosted override).
* **`EMBEDEZ_API_KEY` is no longer used by V3** (the keyless public
  endpoints replaced the paid API) — the repo secret can be deleted; only
  the old V2 script needs it.
* **Docs added:** [`docs/DISCOHOOK.md`](docs/DISCOHOOK.md) (Discohook =
  preview-only here, **fully optional**, safe to disable — and why it isn't
  relied on for posting) and [`docs/CI_SMOKE.md`](docs/CI_SMOKE.md)
  (ci.yml + test_smoke.py = the **required** offline safety gate).

### 🆕 Reddit V3 — round 14 (2026-09-16): card polishing (after the first production runs)

* **Complete galleries incl. GIFs:** the redlib post-page harvest now runs
  **in parallel with the proxy fetch**, and for image posts the complete
  ordered redlib list **wins over the proxy's og: list** — the redditez og:
  tags omit GIFs (a 3-photo + 3-GIF post showed only the 3 photos before).
  Video posts skip the harvest (their DASH chain handles them); when every
  proxy is down the redlib list is still used. No extra time in normal runs
  (the fetches run at the same time).
* **No duplicate gallery items:** the redditez/vxreddit embed pages append
  extra `og:image` tags (the post's "main image", a 140px feed crop, or the
  same photo under a second CDN name). `dedupe_proxy_media` (in
  `testing area/reddit_proxy.py`) drops: the same redd.it **file id**
  (slug/`vN-` variants count as the same file), `width=140`/`crop=1:1`
  crops, and the ONE trailing tag when a page emits N real media + 1 extra.
* **Body text like the redditez card:** every link in the body is now a
  clickable markdown link `[text](url)`, `**bold**` and paragraph breaks are
  kept, and **bare redd.it media URLs are removed from the text** (the media
  already sits in the gallery — fixes the glued
  `…&s=…dc0Seems like the…` text). The og: content values are unescaped
  until stable (fixes `&amp;amp;` in URLs).
* **Crossposts keep working:** the crosspost notice in the RSS content
  ("u/x crossposted this from r/Y — original post") is detected, and the
  media + stats are fetched **from the ORIGINAL post** (a crosspost's own
  pages carry no media — the run-2 crosspost degraded to a plain image
  because vxreddit doesn't resolve crossposts). The card keeps the
  crosspost URL and the "🔁 Crosspost of" line, as before.
* **Missing stats on redditez cards:** the redditez og: page often has no
  stats line (the stats live in the oembed, not the og: tags) — when the
  winning proxy has no stats the bot backfills 💬/👍 from the **Embeddit
  JSON** (one extra request, ~1 s, no bot gate).
* **Embeddit plain-text shape handled:** posts without selftext arrive
  unmarked-up ("Title⬆️ 1.1K • 💬 108" glued on one line, no `<a><b>`
  title) — the parser now handles both shapes and compact numbers
  (`1.1K` → 1100).

### 🆕 Reddit V3 — round 17 (2026-09-17): Arctic Shift search backup

* **Subreddits with NO new RSS posts are re-checked against the Arctic
  Shift archive search API** (`/api/posts/search?subreddit=<sub>&sort=desc
  &md2html=true`, limited to the 48-hour window) — the same post JSON shape
  the crosspost-original lookup already uses. This covers what RSS can't:
  a sub missing from the combined 100-entry feed, per-sub feeds dead or
  bot-walled, or a quiet sub that simply didn't surface.
* **Same pipeline, same guarantees:** archive posts are wrapped as
  feedparser-style entries and run through the SAME `collect()` — the
  dedup cache and the 48h freshness window still apply, so nothing can be
  double-posted. Crossposts found in the archive still get the original
  post's media/stats via the existing crosspost path.
* **Never blocks posting:** the search runs only for subs RSS left empty,
  returns `[]` on any failure (429/timeout/bad shape), and shares the
  existing 3-strike circuit breaker with the crosspost archive lookup.
  First run posts at most one archive post per sub (same anti-flood rule as
  RSS). Log line: `[arctic <sub>] RSS had no new posts — trying N post(s)
  from the archive.`
* Note: Arctic's score/comment counts are stale for ~36 h after a post —
  archive-sourced cards don't present those as live stats (same rule as the
  existing crosspost-original path).
* **Round 18 follow-up (same day, from the live run):** the archive also
  carries posts the moderators soft-removed or the author deleted (a
  removal-notice body instead of content). Those are now detected and
  skipped — not posted and not cached — so they post normally once
  approved.
* **Round 19 follow-up (same day, from the live run — post 1whe2tr):**
  the feed's auto-linker mangled "label line + bare URL" bodies
  (`Firefly video` / `https://b23.tv/…` pairs) into nested `[[U](U)…](U](U)…`
  garbage. A new pre-pass in BOTH body cleaners (RSS + proxy) repairs the
  family to one label line + one clickable URL line per pair (the X-card
  look); nothing else in the body pipeline changed.
* **Round 20 follow-up (same day, from the live run):** two fixes. (1)
  The link fix is now the SIMPLE one: ANY mangle face collapses to ONE
  plain line with the URL once — `Firefly video [https://b23.tv/…](https://b23.tv/…)`
  — exactly like the original post (replaces the round-19 rule; works at
  any nesting depth; clean lines untouched). (2) Archive-sourced posts
  are now verified against the live sources (redditez → vxreddit →
  embeddit → redlib) before posting: a post that is removed, deleted or
  still pending approval is invisible to them, so it is skipped and NOT
  cached — and posts normally once approved/restored.
* **Round 21 follow-up (same day):** the card body now matches the
  original post as RAW text: the mangle fix outputs `label + bare URL`
  (no markdown), clean "label / URL" pairs collapse to ONE raw line, and
  standalone URL lines stay raw — Discord auto-links every bare URL in
  the component v2 container. Clean links, prose and all round 15/16
  shapes untouched.
* **Round 22 follow-up (same day, from the 1whe2tr re-test on the new
  code):** the post's bare URLs can also arrive from a source that
  auto-links them as a clean `label [U](U)` markdown link — the card
  body renders as plain text, so such a link showed its literal
  brackets. URL-labelled links (text == URL) now collapse to the bare
  URL — the original line — and the repaired mangle family outputs the
  bare URL too. Descriptive links (`[text](URL)`, text ≠ URL) and prose
  stay byte-identical.

### 🆕 Reddit V3 — round 23 (2026-09-18): media must win the proxy chain (the 1wj38fc gallery) + removal-notice variants

**What broke (1wj38fc):** `AnantaLeaks/1wj38fc` (posted 19:10Z, a
2-photo gallery, spoilered) was posted at 19:16Z **without any images**
and cached that way. Timeline: at +6 min vxreddit served the title +
stats + body, but its og:image tags had not been rendered yet;
`fetch_proxy_post` accepted that text-only result as "usable" and
**stopped the chain**, so embeddit — which already had both photos — was
never tried; Arctic's media fields were still empty too (it fills
`gallery_data`/`media_metadata` asynchronously after capture); every
other source came up empty; the media-less card was posted and cached,
so no later run ever fixed it.

**The fix (two gates, both in `testing area/`):**

* **Proxy-chain gate (round 23 rule):** `fetch_proxy_post` now returns
  the first service that produces **MEDIA** (photos / GIFs / video). A
  text/stats-only result never stops the chain — it is kept as the
  body/stats fallback and the remaining services still get their shot
  at the media. If no service produces media, the first text-only result
  is returned (text posts post exactly as before). The `need_video`
  video rule is unchanged. Log line:
  `[<key>] <service> returned text only (no media) — continuing the chain for the media.`
* **Arctic media-hint gate (main loop):** if the Arctic record
  positively says the post has media (gallery flags, `post_hint` =
  image/rich_link, `secure_media_domain` on a redd.it media domain, or a
  redd.it media URL) but **no source served any media this run**, the
  post is skipped and **NOT cached** — the next run retries, and once
  the media is available (Arctic's fields filled, or a proxy renders
  the og: tags) the full gallery posts. Bounded by the 48h freshness
  window. Text/link posts have no positive hint and post normally. Log
  line: `archive record says this post has media ... skipping, not cached (retries next run).`

**Acceptance:** images AND content media — still images, GIFs, and
videos — now reach the card for future posts, including spoilered posts
(spoiler images live in the same media fields — `media_metadata` /
gallery data — and in every proxy's media list; verified on 1wj38fc
itself, where embeddit served both of its photos), and the 1wj38fc
failure mode ("posted media-less, cached forever") is closed by the two
gates above.

**22(b) removal-notice variants:**

* A whole title of `[ Removed by moderator ]` (any bold / inner spacing)
  is now a removal marker — before, only whole titles of `[removed]` /
  `[deleted]` were caught (the "removed by moderator" wording only
  matched in the body).
* The "removed by moderators" notice regex now also catches "removed by
  **Reddit**'s filters" / "…Reddit's automated system" (Reddit renders
  filter removals with its own wording).

Both remain deliberately narrow: the title marker must be the *entire*
title, the body notices are only checked in the first 400 characters,
and every skip is *not cached* — so a false positive retries and posts
on a later run instead of being lost.

### 🆕 Reddit V3 — round 24 (2026-09-18): redlib.miningtcup.me joins the fallback fleet

miningtcup — the operator who provided the `nitter.miningtcup.me` RSS
token — also runs **redlib.miningtcup.me** (a redlib front-end for
Reddit; confirmed live in a browser 2026-09-18). It now joins
`REDDIT_RSS_INSTANCES` (after the two reddit.com hosts, ahead of the
three Anubis-gated instances), so it participates everywhere the redlib
instances already do: the per-sub RSS fallback chain, the parallel
post-page gallery harvest, the post's-own RSS feed (test posts), and
the archive-post liveness check.

**DogWAF + the token.** miningtcup's instances sit behind **DogWAF**,
their home-made JavaScript-free WAF that auto-passes current browsers
and challenges scripts. The operator states that DogWAF access tokens
("passes") given out by one instance are valid on their other
instances — and the nitter RSS token comes from that same
infrastructure, so it is very likely such a pass (unverified on redlib —
runs so far show the WAF still rejecting it from GitHub Actions; the
operator has been emailed). The same repo secret
**`NITTER_RSS_TOKEN`** (already set for the Twitter monitor) is now
wired into `reddit_monitor.yml` too, and V3 appends it as `?token=`
to every `redlib.miningtcup.me` request — feeds and post pages alike
(the query-param convention the operator confirmed for nitter).

* **If the token passes the WAF:** redlib.miningtcup.me becomes a
  working instance in the fleet — more redundancy for RSS fallback,
  gallery harvest and the liveness check. Log: `Successfully fetched
  r/<sub> from https://redlib.miningtcup.me` / `gallery via redlib
  (https://redlib.miningtcup.me)`. Nothing else changes.
* **If it doesn't** (the token is scoped to nitter only): the instance
  just logs a bot-check miss and the chain moves on — exactly the
  behavior of the Anubis-gated instances today. One email to
  `nitter-rss@miningtcup.me` / `ted@miningtcup.me` asking for our UA
  to be whitelisted (they have offered this in their Invidious docs
  issue) would fix it — no code change needed after.
* **Nothing else changed:** reddit.com/old.reddit.com stay first, the
  `?feed=` token still applies to reddit.com hosts only, and every
  other path (proxies, FULL MODE, YouTube, crossposts, liveness gate,
  removal filter) runs exactly as before.

**Checked the same day but NOT wired in:** miningtcup's **Invidious**
instance `inv.miningtcup.me` (the `YOUTUBE_MEDIA_EMBED` candidate).
The instance is up and current (v2026.09.13; `/api/v1/stats` is
DogWAF-whitelisted and answers live), but video fetching is broken —
`/watch?v=Yhf9ur3xPQA` shows Invidious's own error page ("This helps
protect our community") instead of the player. The operator self-hosts
and uses it, so this is likely a temporary upstream (YouTube-side)
problem — revisit if/when playback is fixed.

### 🆕 Reddit V3 — round 25 (2026-09-18): most-complete-media-wins (1wj0p83)

**Reported failure:** `AnantaLeaks/1wj0p83` is a 13-photo gallery that was
posted with only one photo and cached. The user-reported workflow-log
reconstruction is: the pre-round-23 run accepted redditez's text-only result
(0 images), never tried vxreddit/embeddit, failed through the redlib mirrors,
and ultimately used the first image in the native RSS fallback. This historical
log reconstruction was supplied by the user, not independently verified here.
Round 23 addressed text-only early stopping; round 25 also addresses a proxy
returning **some but not all** media when a later service can return more.

* **C1 — most media wins:** `fetch_proxy_post` compares all eligible proxy
  services and keeps the largest media list. Ties preserve service priority;
  20 items reach the card capacity (two galleries of ten) and stop the chain
  early. The returned winning list is capped to 20 on a copy, leaving the
  source result unchanged. Health filtering, text-only fallback and video eligibility remain
  unchanged. Logs show `best so far` and `replacing the winner`.
* **C2 — known partial archive galleries retry:** if Arctic's valid structured
  gallery entries outnumber the resolved media, skip without caching. The next
  scheduled run retries within the existing 48-hour window. The gate applies
  to archive entries without native post JSON; video cards, explicit test posts
  and dry runs are exempt, as in the supplied round-25 specification.
  The existing zero-media gate remains in place.

**Limits:** this improves completeness, not a guarantee. An unfilled Arctic
record counts as zero and cannot detect a partial gallery when every available
proxy is also partial. Counts exclude invalid/deleted/unfilled entries. Proxy
results retain the winning source's order; original Reddit order is available
from structured gallery data or an ordered redlib harvest, but cannot be inferred
from an unordered embeddit list alone. No post-specific image ordering is hardcoded.

**Deployment and repair:** after merging this PR in `News-Feed-Embed-Twitter`,
sync `testing area/reddit_proxy.py` and `testing area/reddit_main_v3.py` to the
production `News-Feed-Embed-Reddit` repository. The cached card does not repair
itself. First run that repository's workflow with
`test_post = AnantaLeaks/1wj0p83` and `dry_run = yes`; inspect the payload for
all 13 photos and their order. Only after verification, delete the old Discord
card and run the explicit test post without dry-run. Test posts bypass dedup
and the archive completeness gate, so do not assume a successful run proves
all expected media were retrieved.

### 🆕 Reddit V3 — round 31 (2026-09-20): the feed-token `.json` probe is skipped when there's no OAuth app

**Why:** since round 12, every run that found new posts attempted each post's JSON once with the
personal `REDDIT_FEED_TOKEN` (`www.reddit.com/comments/<id>.json?limit=25&raw_json=1&feed=…`,
65 s `FEEDTOKEN_JSON_STAGGER` wait between attempts) — a FULL-MODE fallback for the no-OAuth-app
case. Live-verified 2026-09-20: Reddit 403s that `.json` route from datacenter IPs (the feed
token's documented role is the RSS rate tier — reddit.com's own docs: "For RSS, you can use the
feed token … to get a higher rate limit"), so without an OAuth app the probe was 65 s of
guaranteed 403 log noise per run with new posts (the first attempt; a 403 is remembered for the
rest of the run). Steady-state runs (no new posts) never reached it — only runs with new posts
paid.

**What changed:** the probe now runs only when it can possibly work:

| `REDDIT_JSON_PROBE` (repo **Variable**, optional — unset = `auto`) | Behavior |
|---|---|
| `auto` (default) | the probe runs **only when BOTH** `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are set — a real Reddit app exists. Without an app: **never** (no 65 s wait, no 403 log line — the code path is skipped). With a working app: the OAuth path serves the JSON anyway (no sleep) — the probe is only the legacy fallback if the app is misconfigured. |
| `force` | legacy behavior — always try once per run with new posts (65 s wait) |
| `off` | never, even with an app |

**FULL MODE later = two secrets, zero code change.** `reddit_monitor.yml` now maps
`REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` **live** (empty secrets are harmless — the script
requires both non-empty). When Reddit's approval form (Responsible Builder Policy) accepts your
app, set the two repo secrets and the next run is FULL MODE — OAuth JSON for every post:
all photos, stats, 💬 OP comment, true crosspost embeds. In `auto` mode the feed-token probe
also switches on as a harmless fallback.

**Numbers (2026-09-20 live audit):** 18-post first run 213 s → ~148 s · 3-post run 121 s →
~56 s · steady-state zero-post run 7 s → 7 s (untouched). The first Discord post in a run with
new posts arrives ~65 s earlier.

**Startup log (native mode, no app):** `No Reddit OAuth app secrets — V3 uses native RSS data;
the feed token .json FULL-MODE probe is skipped (no OAuth app secrets — datacenter IPs 403 the
.json route anyway, so the probe would only cost 65 s + a 403 log line per run with new posts).
Set REDDIT_JSON_PROBE=force to re-enable, or add REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET for
FULL MODE (reddit.com/prefs/apps -> type 'script') — no code change.`

**Nothing else changed:** RSS (combined feed + fallbacks), the proxy media chain, the Arctic
archive backup, YouTube, crossposts, the liveness/removal gates and the `pending_reddit.json`
re-check (round 30) all run exactly as before.

### 🆕 Reddit V3 — round 32 (2026-09-20): queued posts can no longer post early + reason-aware
pending re-check

**Why (all live-verified 2026-09-20):**

1. **Live incident — a queued post was posted early (post `1wl41aj`, "Post is
   awaiting moderator approval."):** the card hit Discord ~1 cron tick after creation while
   the post was still in the mod queue. Root cause: the RSS feed delivers queued posts with
   their **real content** (no banner in the feed text), and the round-20 liveness gate only
   ran for **Arctic**-sourced posts — an RSS-sourced queued post passed every gate. (Arctic
   already had the post, `approved_at_utc: null`; all three live proxies 403/404 it — probed
   the same day — so only the RSS path saw it "clean".)
2. **The 15–20 min zombie runs:** the round-30 pending cache re-checked ~19 **mod-removed**
   posts through the full proxy chain (~13 s each) on **every 30-minute** cycle, until the
   48-hour window expired them.
3. **The approval delay:** queued posts rode the shared 30-min throttle — approval could sit
   up to 30 min before Discord.

**The fixes:**

1. **Liveness gate for ALL sourced posts** (was Arctic-only): before posting, a live source
   (redditez → vxreddit → embeddit, then the redlib post pages) must be able to retrieve the
   post. For RSS candidates the fallback uses the **redlib post pages only** — the feed cannot
   verify the feed (a queued post sits in the feed with real content). A queued post is now
   skipped + **not** cached, re-checked on the short interval, and posted the moment a live
   source can see it. Cost: +1 live probe per new post (~1–5 s — the per-run warm-up skips
   dead services). If ALL live sources are down, new posts wait for recovery — safety first.
2. **Reason-aware re-check** (`_pending_throttle_skip`):

   | Pending reason | Re-check behavior |
   |---|---|
   | `removal_notice` / `removal notice` / `title marker` / `whole-body marker` / `removed by moderator` / `removed by moderators/filters` / `deleted by author` (removed / deleted) | **never re-verified** while the entry exists (self-expires at the 48 h window). A removed post cannot change state while removed — if a mod **restores** it, it re-enters via **RSS** with a fresh `updated` stamp, and the RSS path bypasses the skip so the full pipeline posts it (or re-queues it if a notice is still shown). |
   | `not_live` / `pending approval` / `sources_down` (queued for approval, or a transient all-sources-down miss) | re-checked on the **short** `APPROVAL_RECHECK_SECONDS` interval (default **300 s = 5 min**, repo variable). A newly-approved post then posts on the next cron tick (~3–6 min worst case) instead of up to 30 min. The mod-queue banner itself is now an explicit reason (`pending approval`) — a queued post is never mistaken for live even when a source renders the banner. |
   | `media_wait` / `partial_gallery` | unchanged round-30 behavior: at most every `PENDING_RECHECK_SECONDS` (30 min). |

**No double posts:** a queued post is skipped and NOT added to the dedup cache; on approval
it is posted exactly once and leaves the pending state (`posted.add` + `pending.pop`). The
2026-09-19 P0 concurrency rule (one run per branch; a 2nd run queues and sees the fresh
`posted_reddit.json`) is unchanged — and with runs back to ~7 s the overlap window that rule
protects shrinks further.

**Result (same logs):** the one-time first-detection wave (~19 × 13 s ≈ 2 min) is kept —
that's the safety check proving a post is really removed — every later run returns to the
~7 s steady state even with a removed-post backlog, and a queued post hits Discord ~one cron
tick after approval.

**Nothing else changed:** RSS, the proxy chain, Arctic search, YouTube, crossposts, the
liveness/removal gates and the round-31 probe gate are byte-identical except the lines above.
Only the "is this post live / is this pending post due for a re-check now?" decisions changed.

### 🆕 Reddit V3 — round 34 (2026-09-28): the dedup cache can no longer silently evict a subreddit's keys (AnantaLeaks re-post loop fixed + 4 new guards)

**Why (live incident 2026-09-28, proven from the prod `posted_reddit.json`
commit history):** `AnantaLeaks_1wqhmw1`, `AnantaLeaks_1wqphp3` and
`AnantaLeaks_1wriz86` posted to Discord on **every 5-minute cron run** while
every other sub posted once. `save_posted` had always capped the cache with
`sorted(posted)[-MAX_CACHE_SIZE:]` (`MAX_CACHE_SIZE = 500`) — a
**lexicographic** eviction. Cache keys are `{sub}_{post_id}`, so once the six
tracked subs crossed 500 total keys (the file grew from ~470 to 500 keys
between 2026-09-25 and 2026-09-28), the slice dropped the alphabetically-FIRST
keys on every save — and `AnantaLeaks_*` sorts before `Genshin_Impact_Leaks`,
`Honkai*`, `WutheringWavesLeaks` and `Zenlesszonezeroleaks_`. Each Ananta post
was added right after posting and **evicted in the same save**: the next run's
`unique_key in posted` check missed, the card re-posted, it was re-added,
re-evicted — a silent infinite loop (the save logs nothing). The commit
history proves it: each 5-min save shows exactly `−1 oldest Genshin key, +1
new key` (the Genshin evictions never re-post because those posts are outside
the 48 h feed window), and no `AnantaLeaks_*` key has ever appeared in
`posted_reddit.json` since the cap was crossed.

**The fix — per-subreddit, newest-first retention:**

| What | Pre-round-34 | Round 34 |
|---|---|---|
| Cap | one global 500 | **per sub** `MAX_CACHE_SIZE_PER_SUB` (default **250**) + global backstop `MAX_CACHE_SIZE_TOTAL` (default **10 000**) |
| Eviction order | **alphabetical** (sub name first!) | **newest-first WITHIN each sub** (leet post ids sort chronologically within a subreddit) |
| First sub to lose keys | AnantaLeaks (every save) | nobody — the oldest of an over-quota sub, and that sub alone |
| Ananta's keys at the cap | gone every save | intact (~5 keys vs a 250 quota) |
| Eviction log | none (silent) | a `dedup cache: evicted N oldest key(s)…` warning naming the keys |

250/sub ≈ 8+ days at Genshin's peak rate (the 48 h window needs only days of
history per sub); the 10 000 backstop is never expected to trigger
(6 subs × 250 = 1500). All three knobs are optional repo **Variables** (not
secrets): `MAX_CACHE_SIZE_PER_SUB`, `MAX_CACHE_SIZE_TOTAL`, `MAX_POSTS_PER_RUN`.

**The extra guards ("what else could silently double-post" audit):**

1. **`keep_newest` force-keep** — the save is told which keys were posted
   THIS run and keeps them no matter what (belt and braces on top of the
   per-sub rule, which already keeps newest-first).
2. **Double dedup in the posting loop** — right before the expensive pipeline
   the loop re-checks `unique_key in posted` (a key listed twice in one run's
   feed — new + mod-queue listings — can no longer post twice in one run).
   TEST POST rebuilds are exempt (re-testing a cached post is their whole
   point).
3. **Per-run flood cap** (`cap_new_posts`, `MAX_POSTS_PER_RUN`, default 25) —
   if a run ever finds more than 25 new posts (stale-feed burst, cache loss),
   it posts the **newest 25** and loudly logs the dropped oldest, which retry
   next run inside the 48 h window. Any future cache-loss bug costs one capped
   run + a loud log line instead of an all-night re-post storm.
4. **Save verification** (`_verify_dedup_save`) — after every save (both call
   sites: the no-new-posts early return and the normal tail) the script proves
   the keys posted this run are on disk; a missing one logs a `DEDUP GUARD`
   **error** naming the keys that will re-post. The 2026-09-28 loop would have
   been caught on its very first save.
5. **Load-time saturation warning** — when a sub is within 10 keys of its
   quota (or the total within 10 % of the backstop) the run logs a warning, so
   the next eviction burst is visible before it happens.

**The X engine (twitter_v3.py) got the same treatment:** identical cap
pattern (`sorted(posted_urls)[-MAX_CACHE_SIZE:]`), keys are
`{account}_{tweet_id}` — so the alphabetically-first account (`Ananta_EN`)
would have been the victim at the 500 cap, and the old "keeps the NEWEST
500" comment was factually wrong. The cache was at ~143/500 keys when this
landed (~2–3 weeks of headroom at current volume); it now keeps the newest
250 per account (`MAX_CACHE_SIZE_PER_ACCOUNT`) with the same backstop,
this-run force-keep, save verification (`DEDUP GUARD` error) and saturation
warning.

**Nothing else changed:** RSS (combined feed + fallbacks), the proxy media
chain, the Arctic backup, YouTube, crossposts, the liveness/removal/pending
gates (rounds 18–32) and the P0 double-post concurrency rule
(`cancel-in-progress: false`) are byte-identical. 18 new offline smoke checks
(11 Reddit + 7 X) pin: Ananta-first keys surviving eviction, the per-sub 250
quota, this-run keys always surviving, an under-quota passthrough, the sorted
byte-stable round-trip on disk, the flood cap (newest-25 of 40), and the
wiring of both guards + both save sites.

### 🆕 Reddit V3 — round 36 (2026-09-29): settle window + duplicate-media gate + restore logging

Round 36 closes the gap where a post is live at check time but removed minutes later.

1. **Settle window (`POST_SETTLE_SECONDS`, default 300).** Fresh posts wait without
   state being written and are fully re-evaluated next run. Older and restored posts
   proceed immediately; `TEST_POST_ID`/`DRY_RUN` bypass it; 0 disables it.
2. **Duplicate-media gate (`DUP_MEDIA_GATE`, default on).** Exact reused `i.redd.it`
   files or external destination URLs are compared with the same sub's newest 120
   posted keys in one batched Arctic request. Only an already-posted post can win;
   unknown identities fail open. Duplicates are held 48 h as `duplicate_media`.
3. **Restore and audit visibility.** RSS restores log `RESTORED:` and pending entries
   can include additive `source`, `title`, and `published_ts` fields.

Quiet runs add no calls. New-post runs add at most one batched Arctic lookup. Settle
only delays; duplicate matching uses exact identities; the X engine is untouched.
28 round-36 smoke checks cover behavior, fail-open paths, and workflow wiring.

### 🆕 Reddit V3 — round 38e (2026-09-30): RSS-backed native queue detection

Round 38d added a conservative negative-space hold for native queued posts with no
AutoModerator comment, but it depended on a readable HTML `/new` listing. GitHub Actions
runner IPs often receive 403s or anti-bot challenges from those pages, so the safety signal
was unavailable on the production path and queued posts such as `1wtpgne` could pass the
intentional fail-open boundary.

Round 38e tries the existing `REDDIT_FEED_TOKEN`-authenticated public RSS listings first:
`/r/<subreddit>/new.rss?limit=100&feed=<token>` on `www.reddit.com` and
`old.reddit.com`. It extracts the same `/comments/<id>/` IDs and uses exact RSS `pubDate`
timestamps to calculate the oldest visible entry. A post that is absent from a readable RSS
listing and still within the proven span is held as `pending approval`; a released post that
appears in the listing proceeds immediately.

The existing HTML listing chain remains the fallback, and every unavailable, malformed, or
future-dated signal fails open exactly as before. The per-subreddit listing cache limits the
new lookup to one attempt per run; the feed token is URL-encoded and never written to logs.
No new secret, Variable, workflow input, or dependency is required. Offline smoke fixtures
cover RSS ID extraction, CDATA and malformed dates, future-date fail-open behavior, token URL
construction, and the live fetch/cache tuple.

### 🆕 Reddit V3 — round 38d (2026-09-29): native zero-comment queue detection

Round 37 correctly held posts that exposed the AutoModerator queue-request text, but
some natively queued posts have **zero comments** and therefore no such text. They can
still appear in the RSS/archive candidate data while remaining absent from the public
`/new` listing. Round 38d closes that gap without changing the queue gate's safety
model or adding a network request.

For the existing post page and existing `/r/<sub>/new?limit=100` response, the monitor
parses visible relative ages (`2h ago`, `2 hours ago`, and the compatible bare-element
form). When all of the following are true, it records the existing `pending approval`
reason and re-checks on the normal 300-second interval:

1. the post ID is **not** in a readable `/new` listing;
2. the page has no round-37 queue-request text (that established path is unchanged);
3. the post header age and the listing's **oldest** visible age both parse; and
4. the post age is younger than `oldest listing age + MOD_QUEUE_WINDOW_SECONDS`
   (six hours by default).

The window itself is the conservative tail margin and remains the hard fail-open cap in
the main loop. There is deliberately **no third mod-queue repository Variable**. A
missing page, blind listing, unparseable age, or post outside the proven span returns no
hold; an ID visible in `/new` always releases immediately. Thus an approved
post normally releases on the next short re-check, while a listing/parser failure remains
the same fail-open behavior as round 37 and no hold can persist beyond the existing
window. Fifteen offline smoke checks pin the native path, the round-37 compatibility
path, every fail-open boundary, both age formats, the listing cache shape, and the
reason wiring.

### 🆕 Reddit V3 — round 35 (2026-09-28): NSFW content gate

A BopLeaks ring post (`Genshin_Impact_Leaks_1ws8huc`) reached Discord while
it was still live; Reddit removed it seconds later. Its archive record carried
Reddit's NSFW markers from creation (`over_18=true` and the `"nsfw"`
thumbnail sentinel). A liveness check cannot close that timing window because
it can only reject a post that has already been removed, so round 35 adds an
earlier **content gate**.

For a run with new posts, Reddit V3 makes one keyless, batched Arctic Shift
`/api/posts/ids` request (up to 500 IDs; the monitor's run cap is 25) and reads
exactly two fields from each returned post:

* `over_18 == true`; or
* `thumbnail == "nsfw"`.

Either marker holds the post in `pending_reddit.json` with reason
`nsfw_flag`; the post is not sent to Discord and a loud `NSFW GATE` warning
records both marker values. The pending entry uses the existing 48-hour window
and archive no-recheck path rather than the posted/dedup cache, so rejected
spam cannot evict legitimate history. An RSS reappearance runs the gate again,
allowing a post whose flag was corrected to proceed normally.

The lookup is deliberately **fail-open**: an outage, malformed response or
not-yet-archived ID produces an `NSFW SCAN ... unknown` line and follows the
existing post path. `TEST_POST_ID` also bypasses the gate. For an exceptional
false positive, the optional `NSFW_ALLOWLIST` repository Variable accepts
comma-separated author names or post IDs; it is empty by default and is wired
into the live workflow.

**Spoilers are unchanged.** Reddit stores spoiler state in the separate
`spoiler` field. The gate never reads that field, so a non-NSFW spoiler
(`over_18=false` and no `"nsfw"` thumbnail sentinel) follows the same path as
before. Clean, flagged, spoiler, unavailable-lookup, allowlist, batching,
pending and main-loop wiring cases are pinned by offline smoke tests.

### 🆕 Reddit V3 — round 33 (2026-09-25): URL-labelled links render clean (live 1wpejir + 1wpdxhs)

**Why (live-verified 2026-09-25, r/Zenlesszonezeroleaks_):** two showcase posts —
`1wpejir` (65k) and `1wpdxhs` (57k), M0W1/M2W1 Phoenix / Velina / Remielle vs Scorched
Horizon — ended with a well-formed markdown link whose **label is a bare URL** and whose
**target differs**:

    …was gathered with the help of [https://zzzanalytics.vercel.app/](https://www.youtube.com/redirect?event=video_description&redir_token=…&q=https%3A%2F%2Fzzzanalytics.vercel.app%2F&v=…)

The author copied the link from a YouTube video description — YouTube wraps such links in a
`youtube.com/redirect` URL carrying a ~330-char token. Reddit renders the link fine (label
only); the Discord card printed the **raw link literally** — label, brackets and the whole
redirect blob. Rounds 15–22 intentionally leave descriptive links untouched (round 22 unwraps
only the self-referential `[U](U)` class), so this class had no handler.

**The fix** (in the same clean-line pre-pass as rounds 20/21/22, with round 22's identical
mangle-residue guard, so mangled lines are still the round-20/21 repairers' alone):

| Link shape (clean line) | Before (card) | After (card) |
|---|---|---|
| `[U](U)` — label = target (round 22) | bare `U` | unchanged |
| `[U](V)` — label is a bare URL, target differs (**new**) | raw `[U](V…)` with the ~330-char redirect blob | bare `U` (Discord auto-links it; for a redirect-wrapper target `U` is the real site — the better link) |
| `[label](youtube.com/redirect?…&q=ENCODED)` (**new**) | raw label + blob | `label (decoded destination)` via the wrapper's `q=`/`qp=` param |
| `[label](https://normal-url)` | raw (unchanged by design) | unchanged |

A whole-line `[U](redirect)` now feeds the existing round-21/22 bare-URL merge (joins under
its label exactly like the round-22 class). Everything else is byte-identical: prose-labelled
descriptive links, mangle residue, `[U](U)`, and every gate (liveness, removal, pending,
dedup, concurrency). 8 new offline smoke checks pin the live shape end-to-end
(`_clean_url_texted_links` + `_line_stage` on the exact 1wpejir/1wpdxhs line).

### 🧪 Reddit V3 — final testing & verification procedure (round 12)

**Step 0 — one-time: archive the OLD Reddit V1/V2 workflow (if previously enabled).**
In the **Actions** tab, if the old workflow named **"Reddit Feed Monitor"**
(the old V1 one — its file was also named `reddit_monitor.yml`, a name the V3 monitor has since taken) is listed → its three-dot menu →
**Archive workflow**. It targeted the same channels and the same
`posted_reddit.json` dedup cache as V3, so every time GitHub's native cron
fired it, it would post the same new post in the OLD plain style and
"steal" it from V3. (Your external cron-job.org trigger should point at
**"Reddit Feed Monitor"** — `reddit_monitor.yml` — not the old one.)

Everything is triggered from the repo's **Actions** tab → workflow
**"Reddit Feed Monitor"** → the **Run workflow** button (branch `main`).

**Step 1 — Dry run (safety check; nothing is posted)**

1. Set `dry_run` = **yes**, leave `test_post` **empty** → **Run workflow**.
2. Wait 1–3 minutes and open the run log. It lists every post it *would*
   post, each with its complete card payload. **Discord is NOT touched and
   the cache is NOT saved — that is the whole point of the dry run**
   (a "DRY RUN finished" run intentionally sends nothing).
3. Key lines to see: `Combined feed OK: …`, per post `post JSON …`
   (full or native mode), `video url OK via …` / `gallery via redlib (…)`,
   and `DRY RUN (Discord NOT touched): …` per post.
4. The post the dry run listed will be posted by the **next normal cron run**
   (the dry run doesn't mark it as posted).

**Step 2 — Test posts (re-post specific old posts into the test channel)**

Run the workflow with `dry_run` = **no** and `test_post` =
`<Subreddit>/<post_id>` (one at a time), e.g.:

| `test_post` value | Post type | What to expect in the channel |
|---|---|---|
| `AnantaLeaks/1wguffh` | 3-photo gallery | **all 3 photos**, full-res, never one 140px thumb |
| `AnantaLeaks/1wgq3cy` | YouTube link post | **video only** + the animated YouTube button — no screenshot |
| `HonkaiStarRail_leaks/1wguwvw` | Reddit video | **video tile only** — no duplicate first-frame image |

The log tells you the data source: `post JSON OK via …` (FULL MODE) or
`test post found in the RSS feed` / `test post base via redlib (…)`.

**Step 3 — Normal runs (the real verification)**

Do nothing — the scheduled runs post new posts with the new card. In the test
channel check:

* multi-photo posts → **all** photos (never a single 140px thumbnail)
* video posts → **video tile only** (no duplicate screenshot)
* no raw `redd.it` URLs lingering in the body text
* log: **no** `seaof.glass` lines at all (off by default); if you ever see
  `video url OK via native v.redd.it DASH_720 (…)`, play that video and
  confirm it has **audio** (if it plays silent, report it — the ladder is
  dropped with a one-line change)

**Step 4 — Active engine & switching**

By default, `.github/workflows/reddit_monitor.yml` runs the active V3 engine:
`python "testing area/reddit_main_v3.py"`.
To switch to V1 or V2, change the run line in `.github/workflows/reddit_monitor.yml`:
* `run: python "testing area/reddit_main.py"` (V1, free mirror link)
* `run: python "testing area/reddit_main_v2_embedez.py"` (V2, rich card via EmbedEZ key)
* `run: python "testing area/reddit_main_v3.py"` (V3, native rich card, no key)

### Secrets

| Secret | Value |
|---|---|
| `SUBREDDITS` | Comma-separated subreddit names, e.g. `Zenlesszonezeroleaks_,Genshin_Impact_Leaks,HonkaiStarRail_leaks,WutheringWavesLeaks,HonkaiNexusAnimaLeaks,AnantaLeaks` |
| `WEBHOOK_REDDIT_<SUB>` | One per subreddit's channel (rule: `WEBHOOK_REDDIT_` + UPPERCASE name, non-alphanumerics → `_`). For the default six: `WEBHOOK_REDDIT_ZENLESSZONEZEROLEAKS_`, `WEBHOOK_REDDIT_GENSHIN_IMPACT_LEAKS`, `WEBHOOK_REDDIT_HONKAISTARRAIL_LEAKS`, `WEBHOOK_REDDIT_WUTHERINGWAVESLEAKS`, `WEBHOOK_REDDIT_HONKAINEXUSANIMALEAKS`, `WEBHOOK_REDDIT_ANANTALEAKS` |
| `REDDIT_FEED_TOKEN` *(optional — **recommended**)* | Your personal Reddit **feed token** (round 9): old.reddit.com → your username → **Preferences** (or `old.reddit.com/prefs/feeds`) → any feed link ends with `?feed=<token>` — copy just the token. Moves RSS requests to the logged-in rate tier, making multi-sub monitoring bulletproof. See the round-9 section below. |
| `REDDIT_MIRROR` *(optional — set as a repo **Variable**, not a Secret)* | **V1 only.** Embed mirror host: `redditez.com` (default), `embeddit.deltandy.me`, or `vxreddit.com` |
| `EMBEDEZ_API_KEY` | **V2 only** — from your embedez.com dashboard |
| `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` *(optional — V3)* | Reddit **script app** (reddit.com/prefs/apps → type "script" → redirect `http://localhost`). Enables V3 **FULL MODE** reliably (all photos, stats, OP comment, true crosspost embeds) via OAuth. 2026 note: new API access may require Reddit's approval form — V3 works without it (native mode; the feed-token `.json` probe is skipped while no app exists — round 31). The workflow maps both secrets live: drop them in whenever you get the app and FULL MODE turns on with no code change. |
| `DISCORD_WEBHOOK_URL` *(optional)* | Catch-all fallback |
| `NITTER_RSS_TOKEN` *(optional — repo **Secret**, not a Variable)* | miningtcup's DogWAF token — unlocks the token-gated `nitter.miningtcup.me` RSS instance (X monitor) and `redlib.miningtcup.me` (Reddit V3, appended as `?token=`). Stored as a secret because GitHub masks secrets in every log line but prints variables in plain text. Empty = those instances just log a bot-check miss and the chain moves on (round-12 / round-24 sections). |

**Optional V3 switches** (repo **Variables**, not Secrets — behavior is fine
with none of them set):

| Variable | Default | Meaning |
|---|---|---|
| `YOUTUBE_MEDIA_EMBED` | off | `1` = also try to *play* YouTube links (seaof.glass, +up to ~3 min probes/post); off = thumbnail + `starwardspark3` button |
| `REDDIT_OP_COMMENT` | on | `0` = hide the 💬 OP comment line (FULL MODE) |
| `DISCOHOOK_PREVIEW` | on | `0` = don't create/log the per-card Discohook share-link preview |
| `FEEDTOKEN_JSON_STAGGER` | `65` | seconds between feed-token `.json` attempts (lower only if your token reliably works there) |
| `REDDIT_JSON_PROBE` | `auto` | when the feed-token `.json` FULL-MODE probe runs: `auto` (default) = only when BOTH `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` exist; `force` = always try (legacy, 65 s per run with new posts); `off` = never (round 31) |
| `MAX_CACHE_SIZE_PER_SUB` | `250` | round 34: newest dedup-cache keys kept **per subreddit** (the old single 500 global cap evicted AnantaLeaks keys alphabetically once crossed — the 2026-09-28 re-post loop) |
| `MAX_CACHE_SIZE_TOTAL` | `10000` | round 34: global backstop for the dedup cache (never expected to trigger with 6 subs) |
| `MAX_POSTS_PER_RUN` | `25` | round 34: per-run flood cap — the newest N new posts post, the rest retry next run inside the 48 h window (loud `POST FLOOD GUARD` log line) |
| `MAX_CACHE_SIZE_PER_ACCOUNT` | `250` | round 34 (X engine): newest dedup-cache keys kept per account (same latent cap bug as Reddit — `Ananta_EN` would have been the victim at 500) |
| `NSFW_ALLOWLIST` | *(empty)* | round 35: optional comma-separated Reddit author names or post IDs that bypass the NSFW content gate; empty = no exceptions |
| `POST_SETTLE_SECONDS` | `300` | round 36: seconds a new post must survive before posting; 0 = off |
| `DUP_MEDIA_GATE` | `1` | round 36: same-sub exact-media duplicate gate with posted-post-only winners; 0 = off |

### The workflow (`.github/workflows/reddit_monitor.yml`)

```yaml
name: Reddit Feed Monitor

concurrency:                  # P0 double-post fix (2026-09-19): one run per branch
  group: check-reddit-${{ github.ref }}
  cancel-in-progress: false   # a run can sit between "posted" and "cache committed"

on:
  workflow_dispatch:          # allows manual + external-cron triggering
    inputs:
      test_post:
        description: 'Optional TEST POST: rebuild ONE specific post, e.g. AnantaLeaks/1wgvcz7 (native RSS/redlib fallback if the post JSON 403s). Leave empty for a normal run.'
        required: false
        default: ''
      dry_run:
        description: 'Dry run: build + log the payloads, but do NOT post to Discord and do NOT save the cache. Useful before promoting.'
        type: choice
        options: ['no', 'yes']
        required: false
        default: 'no'

permissions:
  contents: write

jobs:
  check-reddit:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v7   # v7 = Node 24 runtime (v4/v5 ran on deprecated Node 20)

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: '3.14.7'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Reddit Feed Monitor
        env:
          SUBREDDITS: ${{ secrets.SUBREDDITS }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          REDDIT_FEED_TOKEN: ${{ secrets.REDDIT_FEED_TOKEN }}   # your Reddit feed token (recommended — old.reddit.com -> Preferences -> Feeds)
          NITTER_RSS_TOKEN: ${{ secrets.NITTER_RSS_TOKEN }}     # miningtcup token (stored as secret to mask from logs)
          TEST_POST_ID: ${{ github.event.inputs.test_post }}
          DRY_RUN: ${{ github.event.inputs.dry_run == 'yes' }}
          WEBHOOK_REDDIT_ZENLESSZONEZEROLEAKS_: ${{ secrets.WEBHOOK_REDDIT_ZENLESSZONEZEROLEAKS_ }}
          WEBHOOK_REDDIT_GENSHIN_IMPACT_LEAKS: ${{ secrets.WEBHOOK_REDDIT_GENSHIN_IMPACT_LEAKS }}
          WEBHOOK_REDDIT_HONKAISTARRAIL_LEAKS: ${{ secrets.WEBHOOK_REDDIT_HONKAISTARRAIL_LEAKS }}
          WEBHOOK_REDDIT_WUTHERINGWAVESLEAKS: ${{ secrets.WEBHOOK_REDDIT_WUTHERINGWAVESLEAKS }}
          WEBHOOK_REDDIT_HONKAINEXUSANIMALEAKS: ${{ secrets.WEBHOOK_REDDIT_HONKAINEXUSANIMALEAKS }}
          WEBHOOK_REDDIT_ANANTALEAKS: ${{ secrets.WEBHOOK_REDDIT_ANANTALEAKS }}
          # OPTIONAL (V3 FULL MODE): Reddit script app — 2026: new API access
          # may require Reddit's approval form. Round 31: wired LIVE (empty
          # secrets are harmless); set both = FULL MODE, no code change.
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          # Round 31: feed-token .json FULL-MODE probe — auto (default, only
          # with the OAuth app above) | force (always, legacy 65 s) | off.
          REDDIT_JSON_PROBE: ${{ vars.REDDIT_JSON_PROBE }}
          # Round 35: comma-separated NSFW-gate author/post-ID exceptions.
          NSFW_ALLOWLIST: ${{ vars.NSFW_ALLOWLIST }}
        # While testing a new version, point this line at the test copy instead
        # (QUOTES REQUIRED — the folder name has a space):
        #   run: python "testing area/reddit_main_v3.py"
        # Switch between engines:
        #   run: python "testing area/reddit_main.py"            <- plain V1 (free, mirror link)
        #   run: python "testing area/reddit_main_v2_embedez.py"  <- rich card (EmbedEZ key)
        run: python "testing area/reddit_main_v3.py"   # ← V3 (proxy media + native fallback)

      - name: Persist updated caches (retry safely on a concurrent main update)
        env:
          CACHE_BRANCH: ${{ github.ref_name }}
        run: |
          set -o pipefail
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add -f posted_reddit.json proxy_health.json pending_reddit.json

          if git diff --cached --quiet; then
            echo "No cache changes to push."
          else
            if ! git commit -m "auto: update posted_reddit.json + proxy_health.json + pending_reddit.json caches"; then
              echo "::error::CACHE COMMIT FAILED — dedup cache was not persisted; rerun this monitor after resolving the repository state."
              exit 1
            fi

            cache_branch="${CACHE_BRANCH:-main}"
            pushed=0
            attempts=0
            for attempt in 1 2 3; do
              attempts="$attempt"
              if git push origin "HEAD:${cache_branch}"; then
                pushed=1
                break
              fi

              # A remote cache commit may have landed between checkout and push.
              # Rebase our single cache commit, then retry with bounded backoff.
              if [ "$attempt" -lt 3 ]; then
                echo "::warning::Cache push attempt $attempt/3 failed; rebasing ${cache_branch} before retry."
                if ! git pull --rebase origin "$cache_branch"; then
                  git rebase --abort || true
                  echo "::error::CACHE PUSH RECOVERY FAILED — rebase could not complete; dedup cache was not persisted."
                  break
                fi
                sleep "$((attempt * 15))"
              fi
            done

            if [ "$pushed" -ne 1 ]; then
              echo "::error::CACHE PUSH FAILED after ${attempts}/3 attempt(s) — dedup cache was not persisted; the next run may re-post. Rerun this monitor after GitHub recovers."
              exit 1
            fi
          fi

```

Create `posted_reddit.json` with `[]` as its initial content (first run posts only the newest item,
by design). Proxy warm-up states are tracked in `proxy_health.json`; skipped posts (removed /
pending approval / media still missing) wait in `pending_reddit.json` and are re-checked live
(round 30). If `RETRACT_DEAD_POSTS=1` is enabled, the Reddit workflow also persists
`posted_messages.json` with the Discord message ID, delivery metadata, and payload needed for an
optional edit/delete tombstone. It is pruned by `RETRACT_WINDOW_SECONDS`, is ignored locally, and
is force-added only by the workflow.

## 🆕 Reddit behaviors (2026-09-11 update)

* **Buttons were trimmed.** The Embeddit and vxReddit mirror buttons are **gone** (see concerns §6),
  and *Read Post* now points to the **original `https://www.reddit.com/...` permalink** — not the
  redditez mirror. Mirrors stay credited at the top of this README.
* **Switching the V1 embed mirror (redditez ⇄ Embeddit  vxReddit).** By default V1 posts the
  redditez link (plain reddit links don't unfurl richly via plain webhooks). All three mirrors
  accept the **same** `/r/<sub>/comments/…` path format and were verified live (2026-09-12) to
  serve embed meta to Discordbot, so switching is pure configuration — no code edit:
  1. Repo → **Settings → Secrets and variables → Actions → *Variables* tab** → new variable
     **`REDDIT_MIRROR`** = `embeddit.deltandy.me` or `vxreddit.com` (full `https://…/` URLs are
     tolerated; they're normalized down to the host).
  2. In `reddit_monitor.yml` make sure the env block contains
     `REDDIT_MIRROR: ${{ vars.REDDIT_MIRROR }}` (if running V1).
  3. Next run uses the new mirror. Switch back anytime by setting the variable to `redditez.com`
     (or deleting it).
  **Reddit V2 needs nothing** — it fetches post data from the EmbedEZ API and builds its own
  Components V2 card, so no mirror is involved at all.
* **YouTube posts get a playable embed (V1).** If the thread body links to YouTube (`watch?`,
  `shorts/` or `youtu.be`), the bare YouTube URL is appended on its own line after the redditez
  link — verified to auto-embed a working YouTube player alongside the reddit embed. A conditional
  **▶️ YouTube button** is also added. On V2 the URL appears as a clickable line plus the same
  button (Components V2 messages cannot auto-unfurl links — Discord limitation).
* **Pending-approval / mod-queue posts are never left out.** Subreddits with a moderator queue only
  publish posts to the `new` RSS listing **when approved** — sometimes hours or a day later. Two
  safeguards cover this: the freshness window was widened from 3h to **48h** (`MAX_AGE_SECONDS`), and
  the age check uses the RSS *updated* timestamp whenever it's newer than *published* (an approval
  bumps `updated`). A thread approved "tomorrow" still arrives. If your subs regularly take longer
  than 48h to approve, raise `MAX_AGE_SECONDS` near the top of the script.
* **Reddit V2 fixes** — all EmbedEZ text fields are now HTML-sanitized (their authorized
  `content.title` itself contains raw `<a>`/`<br>`
  tags, which previously rendered literally), and
  the stats line ends with a 🕐 `<t:…:f>` timestamp (from EmbedEZ `postedDate`, falling back to the
  RSS date).

## ⚠️ Reddit V2 (Components V2) — concerns you should know

The V2 script was rebuilt against the **currently documented** EmbedEZ API, but please read these
points before relying on it:

1. **The API key is not fully free.** The embedez dashboard shows a *credits* balance (fresh accounts
   start around 100 credits; more requires payment, and payments "may take up to 5 minutes to
   process"). **Every new post costs 2 API calls** (one `search` + one `preview`). If you don't want
   to spend credits, just use **Reddit V1** — it needs no key at all.
2. **Documented two-step flow.** V2 uses only the endpoints in the current OpenAPI docs:
   `GET /api/v1/providers/search?url=…` → returns a `key`, then
   `GET /api/v1/providers/preview?search_key=…` with header `Authorization: Bearer <ez_key>`.
   The older unofficial `/providers/combined?q=` endpoint from early docs is **no longer documented**
   and is not used.
3. **Graceful no-key fallback.** Without a valid key, the preview endpoint still returns *public* data
   (author, title, one thumbnail). V2 detects that and posts a **limited card** with a small
   `ℹ️ Limited preview` note instead of skipping the post.
4. **Defensive field parsing.** Media URLs are read from `media[].url` **or** the legacy
   `media[].source.url` shape; HTML in preview titles is stripped automatically. Even so —
5. **EmbedEZ warns the API may break.** Their docs explicitly say *"large changes will be made to the
   API in the future, and these might break the current API."* If posts suddenly fail, read the Actions
   log — it prints the exact API response — and check their release notes/docs for field renames.
6. **The Embeddit / vxReddit buttons were removed (2026-09-11).** A true
   "click to switch embed mirror" rotation is impossible via webhooks — interactive buttons need a
   24/7 bot process answering Discord interactions, incompatible with this stateless design — and the
   always-visible duplicate mirror buttons added clutter without value. The mirrors remain fully
   credited at the top of this README.
7. **HTML is stripped from every text field.** With a valid API key, EmbedEZ's `content.title` itself
   contains HTML (`Posted in <a …>r/sub</a>
…`) — earlier builds rendered those tags literally in
   the Discord card. All title/description/text fields (authorized *and* public-preview) are
   sanitized now.
8. **Components V2 can't auto-unfurl a bare YouTube link** inside a card (the auto-embed player is a
   V1 behavior Discord only applies to regular message content). V2 therefore shows the YouTube URL
   as a clickable line plus a ▶️ YouTube button; if you want the playable inline player, use
   **Reddit V1**.

## 🔧 Reddit V1 fix (2026-09-11) — why the first run failed

Your first V1 test logged `Could not fetch valid RSS feed for r/*** from any instance.` The cause was
verified live:

| Source (in code order) | Result |
|---|---|
| `redlib.perennialte.ch` | **HTTP 403** — Cloudflare "Just a moment…" challenge |
| `old.reddit.com` | HTTP 200 but an **HTML "Welcome to Reddit" interstitial**, zero RSS entries |
| `www.reddit.com` | ✅ **real Atom feed, 25 entries** — but it wasn't in the source list! |

`reddit_main.py` (and V2) now:
* try **`https://www.reddit.com/r/<sub>/new/.rss` first**, with `old.reddit.com` and redlib as fallbacks;
* **validate** the response actually contains `/comments/` permalinks before accepting it (old.reddit's
  HTML page is now properly rejected);
* **log exactly why each source was skipped**, so future breakage is diagnosable from the Actions log.

If `www.reddit.com` ever starts blocking GitHub's datacenter IPs for you, open the Actions log —
you'll see the per-source reasons — and just reorder/replace entries in `REDDIT_RSS_INSTANCES`.

### 🆕 2026-09-12 — dead Redlib instance + HTTP 429 fixes (all subreddits at once)

With all six subreddits monitored simultaneously, two live issues surfaced:

| Problem | What the Actions log showed |
|---|---|
| `redlib.perennialte.ch` **shut down** (31 Aug 2026 — "long-term unreliability") | `[https://redlib.perennialte.ch] HTTP 410 for r/… — trying next source.` |
| `www.reddit.com` **rate-limits parallel fetches** (six subs hit in the same second) | `[https://www.reddit.com] HTTP 429 for r/… — trying next source.` for most subs; only one or two got through |

Both Reddit scripts now:
* **retry once on HTTP 429** after `RATE_LIMIT_RETRY_DELAY` (6s) before falling through to the
  next source;
* **stagger the fetch starts** by `FEED_FETCH_STAGGER` (1.2s between subreddits) so the six feeds
  no longer fire simultaneously;
* use a **fresh Redlib fallback chain** from the official instance list (checked 2026-09-12):
  `safereddit.com` → `red.artemislena.eu` → `redlib.privacyredirect.com` → `redlib.privadency.com`
  → `redlib.nadeko.net` → `redlib.ducks.party` → `redlib.catsarch.com` → `snoo.habedieeh.re`
  (note: `safereddit.com` filters NSFW — harmless as a fallback for these subs).

A missed run loses nothing: the 48-hour window still catches any post on a later run. If Reddit
ever blocks GitHub's datacenter IPs more aggressively, or a Redlib instance dies, the Actions log
shows exactly which source answered what — just reorder/replace entries in `REDDIT_RSS_INSTANCES`
(the V3 list additionally keeps the optional token-gated miningtcup host).

### 🆕 2026-09-13 — round 9: one combined RSS request + feed token + verified mirrors

Live testing on 2026-09-13 confirmed how strict Reddit's datacenter rate limiting has become
(anonymous RSS ≈ **1 request/minute per IP** since June 2026 — a burst of 7 requests 429'd
entirely; one request 65s later succeeded), and that **every public Redlib/Eddrit mirror is now
bot-walled** (every official registry instance was probed: Anubis "Verifying your browser…"
challenges, 418 bot-checks, Cloudflare 403s, 404s, dead SSL). So round 9 does three things:

1. **ONE combined feed request per run (the big fix).** Reddit joins subreddits with `+` in one
   URL, and it's verified live that this works with the `?limit=100` parameter (default 25, max 100):
   ```
   https://www.reddit.com/r/Zenlesszonezeroleaks_+Genshin_Impact_Leaks+HonkaiStarRail_leaks+WutheringWavesLeaks+HonkaiNexusAnimaLeaks+AnantaLeaks/new.rss?limit=100
   ```
   → **200, real Atom, ~190 KB, posts from all active subs in a SINGLE request.** One request per
   run fits inside the ~1/min anonymous limit by itself. Each entry's permalink still names its
   subreddit, so **per-channel webhook routing is unchanged** (and the existing
   `posted_reddit.json` dedup keys still match). If the combined feed ever fails, the script
   **automatically falls back** to the old per-subreddit fetches (instance rotation + retries).
2. **`REDDIT_FEED_TOKEN` (repo secret — recommended, optional).** Your personal feed token:
   1. Log in at **old.reddit.com** → click your username → **Preferences** (or open
      `https://old.reddit.com/prefs/feeds`).
   2. Any feed link on that page ends with `?feed=<token>` — copy just the token value.
   3. Add it as the secret **`REDDIT_FEED_TOKEN`** (Settings → Secrets and variables → Actions).
      The script appends `&feed=<token>` to native reddit.com requests, moving them to the
      logged-in rate tier — 429s should then essentially stop. (Don't paste the token in chat;
      treat it like a password.)
3. **Fallback mode hardened.** Per-subreddit fallback now retries 429s **twice** (after 6s *and*
   after 45s — the 45s wait rides out the ~1-minute anonymous window refill), and the fallback
   instance list was trimmed to the 5 sources that at least respond
   (`www.reddit.com`, `old.reddit.com`, `safereddit.com`, `red.artemislena.eu`,
   `redlib.privacyredirect.com`). The dead/404/418 instances were dropped; all remaining Redlib
   entries are verified-behind-bot-check "lottery tickets" only. Refresh candidates anytime at
   [redlib-instances](https://github.com/redlib-org/redlib-instances).

**Expected Actions log (round 9, with token):** `Fetching combined feed for 6 subreddits in 1
request...` → `Combined feed OK: NN entries covering N subreddit(s).` → posts per channel.

**X side: no changes.** The `RSS_INSTANCES` Nitter list in all `main*.py` files was retested
2026-09-13 and intentionally left exactly as the original repo's (`nitter.perennialte.ch` has the
best GitHub-runner track record; the rest are fallbacks).

---

## 🔗 Discohook integration (round 12)

[Discohook](https://discohook.app) is a free, public Components-V2 message
designer/previewer. V3 uses its **keyless public API** (`POST
https://discohook.app/api/v1/share`): after each successful Discord post it
creates a **share link that renders the exact card** and logs the URL in the
workflow run (`Discohook preview for <key>: https://discohook.app/?share=…`).
That's a fast way to verify a card in the browser while reviewing the log
before promoting a version.

* **No key, no account, no webhook execution** — Discohook's public API has no
  authenticated "send" endpoint (they plan one), so the monitor still posts
  straight to your Discord webhooks; Discohook is preview-only here.
* **Privacy:** the share payload contains only the public card content.
  **No `targets` are sent, so your webhook URL never leaves the repo.** Links
  are public while alive (7-day TTL; share IDs are reused after expiry), so
  don't pin them permanently.
* Disable with `DISCOHOOK_PREVIEW=0`; the share call is best-effort — if
  Discohook is down, the post still goes out and only the preview is skipped.
* Also available (not wired into the monitor): the `/unfurl?url=…` endpoint
  (a re-implementation of Discord's link scraper — handy for debugging how a
  bare URL would embed) and the `discohook.app` website itself for designing
  cards by hand.

## 🤖 Dependabot — automatic dependency updates (optional, free)

This repo ships a ready-made, safe Dependabot setup:

| File | Role |
|---|---|
| `.github/dependabot.yml` | The switch: weekly **pull requests** for `requirements.txt` (pip) + `.github/workflows` (GitHub Actions). **Delete this file to disable — the monitor is unaffected.** |
| `.github/workflows/ci.yml` | The safety gate: every PR (including Dependabot's) must pass `pip install` + `compileall` + `tests/test_smoke.py` before it can be merged. |
| `.github/workflows/dependabot_auto_merge.yml` | **Opt-in** auto-merge of Dependabot PRs once all checks are green. Disabled until you set the repo variable `AUTO_MERGE_DEPENDABOT=yes`. |
| `docs/DEPENDABOT.md` | The **full explanation**: what it is, what it does, what it never does, whether it's optional (yes, 100%), costs/limits, and both ways to enable auto-merge. |

**Short version:** Dependabot is free, built into GitHub, needs no token, and
**only opens PRs — it never touches `main` until you merge** (or explicitly
enable the gated auto-merge). Your monitor keeps running exactly as before in
the meantime.

### 🐍 Python runtime: deliberately pinned, not silently floated

All executable workflows now use exact stable **CPython 3.14.7**. Dependabot
updates pip packages and Action versions, but it does **not** update a
workflow's `python-version` input; that runtime is intentionally reviewed in a
normal PR and proven by CI before it reaches a live posting run. See
[the Python runtime policy](docs/PYTHON_RUNTIME.md) for current-version status,
compatibility, realistic performance expectations, rollback, and the complete
safe-update procedure.

---

# 🛠 Full Setup Guide

## Step 0 — Make the repo your own (**do NOT fork**)

Forked repos get Actions/schedules disabled and auto-disabled again after ~60 days of inactivity —
your bot would silently stop. Instead:

1. On the source repo: **Code → Download ZIP**, then unzip locally.
2. Create a **brand-new empty repository** on your GitHub account.
3. Click *"uploading an existing file"* and drag in **all** files — including the hidden `.github`
   folder (enable *show hidden files* in your file explorer first!).
4. Commit. Since it's a fresh, non-fork repo, workflow **read/write** permissions work out of the box
   (verify at *Settings → Actions → General → Workflow permissions → Read and write*).

## Step 1 — Create Discord webhooks (one per channel)

For each target channel: *Channel Settings → Integrations → Webhooks → New Webhook → Copy URL.*

## Step 2 — Add repository secrets

*Repo → Settings → Secrets and variables → Actions → New repository secret*, then add the ones you
need from the X and Reddit tables above (`ACCOUNTS`, `WEBHOOK_<ACCOUNT>` per account, `SUBREDDITS`,
`WEBHOOK_REDDIT_<SUB>` per subreddit, `EMBEDEZ_API_KEY` only if using Reddit V2, optional
`DISCORD_WEBHOOK_URL` fallback, and **recommended** `REDDIT_FEED_TOKEN` — see the round-9 section
for the 2-minute how-to).

Then, if you use the V1 embed mirror switch, create the repo **Variable** `REDDIT_MIRROR`
(Variables tab, not Secrets).

## Step 3 — Reset the caches for a fresh start

Edit `posted_tweets.json` and `posted_reddit.json` to contain just:

```json
[]
```

On the first run the bots post only the **single newest item** per account/subreddit (by design — no
channel flooding).

## Step 4 — Reliable 10-minute automation (external trigger)

GitHub's built-in `schedule:` can lag 15–60 min or skip runs under load, so we replicate the original
author's "Manually run by …" pattern with a free external cron:

1. **Create a PAT:** GitHub → *Settings → Developer settings → Personal access tokens (classic) →
   Generate new token* → check **`workflow`** (and `repo` if private) → copy it.
2. Sign up at [cron-job.org](https://cron-job.org) (free) and create a job **per workflow**:
   * **URL:**
     `https://api.github.com/repos/<YOU>/<REPO>/actions/workflows/twitter_monitor.yml/dispatches`
     (and a second job for `reddit_monitor.yml`)
   * **Method:** `POST` · **Crontab:** `*/10 * * * *`
   * **Headers:**
     | Key | Value |
     |---|---|
     | `Authorization` | `token <YOUR_PAT>` |
     | `Accept` | `application/vnd.github+json` |
     | `Content-Type` | `application/json` |
     | `X-GitHub-Api-Version` | `2026-03-10` *(optional, future-proof)* |
   * **Body:** `{"ref":"main"}` (match your default branch name)
3. **Perform test run** → expect `204 No Content` (or `200 OK`), then check the Actions tab for a run
   labeled *Manually run by you*. `401` = bad token/scope; `404` = wrong repo/workflow/branch name.

⚠️ **Round 12 (2026-09-17): the in-file `schedule:` is now DISABLED — do not
re-add it while cron-job.org runs.** It raced the external trigger (same
pre-cache commit checked out twice → the same post went out twice and the
2nd cache push was rejected, 2026-09-17). Both monitor workflows ship with
the `schedule:` lines commented out + a re-enable note; to re-enable,
uncomment the two lines **and** pause the cron-job.org job.

## Step 5 — Test end-to-end

*Actions → select the workflow → Run workflow*, then check: the right Discord channels got the right
posts, buttons render, and the cache file shows a new `github-actions[bot]` commit.

For any **new or updated script**, test it from the `testing area/` folder first — see the
[Testing area guide](#-testing-area--how-updates-are-tested-before-going-live) above.

## (Optional) Render Cron instead of GitHub Actions

Create a **Cron Job** on Render: build `pip install -r requirements.txt`, command
`python "testing area/twitter_v3.py"` (or `python "testing area/twitter_v1.py"` / any other engine file), schedule `*/10 * * * *`, and add the same env vars there.

---

## 💻 Local Testing

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in your values
```

`.env` example:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
ACCOUNTS=TYPEII_EN,PomPom_HonkaiSR,Wuthering_Waves,HonkaiNA,Ananta_EN
WEBHOOK_TYPEII_EN=https://discord.com/api/webhooks/...
WEBHOOK_POMPOM_HONKAISR=https://discord.com/api/webhooks/...
WEBHOOK_WUTHERING_WAVES=https://discord.com/api/webhooks/...
WEBHOOK_HONKAINA=https://discord.com/api/webhooks/...
WEBHOOK_ANANTA_EN=https://discord.com/api/webhooks/...
SUBREDDITS=Zenlesszonezeroleaks_,Genshin_Impact_Leaks,HonkaiStarRail_leaks,WutheringWavesLeaks,HonkaiNexusAnimaLeaks,AnantaLeaks
WEBHOOK_REDDIT_ZENLESSZONEZEROLEAKS_=https://discord.com/api/webhooks/...
WEBHOOK_REDDIT_GENSHIN_IMPACT_LEAKS=https://discord.com/api/webhooks/...
WEBHOOK_REDDIT_HONKAISTARRAIL_LEAKS=https://discord.com/api/webhooks/...
WEBHOOK_REDDIT_WUTHERINGWAVESLEAKS=https://discord.com/api/webhooks/...
WEBHOOK_REDDIT_HONKAINEXUSANIMALEAKS=https://discord.com/api/webhooks/...
WEBHOOK_REDDIT_ANANTALEAKS=https://discord.com/api/webhooks/...
REDDIT_MIRROR=redditez.com   # optional, V1 only: embeddit.deltandy.me | vxreddit.com
EMBEDEZ_API_KEY=ez_...       # Reddit V2 only
NITTER_RSS_TOKEN=            # optional — unlocks token-gated nitter/redlib instances
REDDIT_FEED_TOKEN=           # optional (recommended) — old.reddit.com/prefs/feeds, the ?feed= value
# REDDIT_JSON_PROBE=auto     # round 31: feed-token .json probe — auto | force | off
# MAX_CACHE_SIZE_PER_SUB=250       # round 34: dedup-cache retention, per subreddit
# MAX_CACHE_SIZE_PER_ACCOUNT=250   # round 34 (X engine): dedup-cache retention, per account
# MAX_CACHE_SIZE_TOTAL=10000       # round 34: global dedup-cache backstop
# MAX_POSTS_PER_RUN=25             # round 34: per-run flood cap (newest N; the rest retry)
# NSFW_ALLOWLIST=                  # round 35: optional NSFW-gate author/post-ID exceptions
# POST_SETTLE_SECONDS=300          # round 36: settle window (0 = off)
# DUP_MEDIA_GATE=1                 # round 36: exact-media duplicate gate (0 = off)
# MOD_QUEUE_GATE=1                 # rounds 37/38d/38e: mod-queue gate (0 = off)
# MOD_QUEUE_WINDOW_SECONDS=21600   # age/fail-open cap + listing-tail margin
#                                  # (there is no third mod-queue Variable)
```

Then run any engine:
* **X/Twitter:** `python "testing area/twitter_v1.py"` / `python "testing area/twitter_v2_button_outside.py"` / `python "testing area/twitter_v3.py"`
* **Reddit:** `python "testing area/reddit_main.py"` / `python "testing area/reddit_main_v2_embedez.py"` / `python "testing area/reddit_main_v3.py"`

> When a script sits in `testing area/`, quote the path (the space):
> `python "testing area/reddit_main_v3.py"`.

---

## 🚨 Troubleshooting

* **Buttons don't render.** Every webhook POST must use the query param `?with_components=true` —
  Discord *silently drops* components without it (already handled in all scripts; don't remove it).
  Rich-card versions also set the `IS_COMPONENTS_V2` flag (`1 << 15`).
* **An X run logs `… — trying next` for every instance / `NO working nitter
  instance this run` / `ALL FEEDS FAILED this run`** — the whole nitter
  fleet was down/stale (it happened 2026-09-17: the monitor missed tweets
  with zero log lines until round 12 made the path visible). Check
  [status.d420.de](https://status.d420.de/) and refresh `RSS_INSTANCES` in
  `testing area/twitter_v3.py` (verified-fresh first); for a token-gated
  instance set the `NITTER_RSS_TOKEN` secret (round-12 section above). To
  rebuild one specific missed tweet meanwhile: *Run workflow* →
  `test_tweet` = `screen_name/tweet_id`.
* **`Could not fetch valid RSS feed for @…` / `r/…`** — public mirrors rotate/die. For Reddit, see
  the *Reddit V1 fix* section and read the new per-source log lines.
* **`HTTP 429 for r/…` lines in a Reddit run** — Reddit's anonymous datacenter rate limit
  (~1 request/minute per IP since June 2026). Round 9 makes the primary fetch a **single combined
  request** for all subreddits, which normally fits the limit; in fallback mode the script retries
  twice (6s, then 45s) before moving on. A subreddit that still ends up "from any instance" loses
  nothing — the 48h window catches it on a later run. **The permanent fix is the
  `REDDIT_FEED_TOKEN` secret** (round-9 section above) — with it, 429s should essentially stop.
* **`ValueError: invalid literal for int() with base 16: 'None'`** — old V3 bug when FxTwitter returns
  `"color": null`; fixed via the `accent_from_color()` helper with a safe Twitter-blue default.
* **`Deprecation` / `Node.js 20 is deprecated` warnings in Actions logs** —
  these appeared while the workflow still pinned old action versions
  (`actions/checkout@v4`, `actions/setup-python@v5`, which run on the
  deprecated Node 20 runtime). Dependabot's github-actions bump to **v7**
  (Node 24 runtime) removed them — see the Node 20→24 FAQ in
  [`docs/DEPENDABOT.md`](docs/DEPENDABOT.md). Cosmetic either way; your
  Python scripts are unaffected.
* **No run at 10-minute marks** — GitHub's native cron is best-effort; that's why the external
  cron-job.org trigger exists. Round 12 (2026-09-17): the in-file `schedule:` is disabled in both
  monitor workflows — cron-job.org is the single scheduler (the two had
  raced: same pre-cache commit → double post, 2026-09-17). Also note GitHub
  auto-disables `schedule:` after 60 days of repo inactivity — the cache
  auto-commits usually count as activity, and the external trigger is immune.
* **Reddit V2 posts "Limited preview" cards** — your `EMBEDEZ_API_KEY` is missing/invalid or out of
  credits; add a valid key (and watch the credit balance), or switch to free V1.
* **First run posts only one item per account** — intentional anti-flood behavior; normal backfill
  starts on subsequent runs.
* **A big video shows as a thumbnail / "smaller version" note (X V2/V3)** — intended behavior:
  the file exceeded the verified ~256 MB Discord gallery limit (e.g. 4K or very long videos). The
  card still plays a smaller rendition, or links out to X when even that is too big. Tune
  `VIDEO_SIZE_LIMIT` at the top of the script if Discord's behavior ever changes.
* **A video tile says "image not found" (X V2/V3)** — rare, transient Discord proxy hiccup at fetch
  time (not a URL or size problem — the same URL plays fine when re-posted, verified 2026-09-13).
  The old message can't be repaired, so: delete it → remove that tweet's line from
  `posted_tweets.json` → re-run the workflow (or wait for the next run). Full details in the
  round-10 section. If it ever becomes frequent, set `GALLERY_VIDEO_LIMIT` to a smaller proven size.
* **`Discord error 400 ... {"components": ["0"]}`** — old round-3 bug: a tweet with empty body (or
  over-length text) emitted an invalid empty text component. Fixed in round 4 — text is chunked and
  empty components are never sent. If it ever recurs, the Actions log prints the full Discord
  response next to the tweet ID.
* **A GIF shows as a video player instead of an animated image** — every GIF converter was
  unreachable at post time (the log shows `No GIF converter answered ... keeping mp4 player`), so
  the mp4 was kept as the safe fallback. Round-11 chain: `gif.fxtwitter.com` `.webp` →
  `gifconvert.vxtwitter.com` `.webp` → `gifconvert.vxtwitter.com` `.gif` → **fastgif**
  (offline since 2026-09-17, last probe only); the log names the winner
  (`gif.fxtwitter.com down; using gifconvert for ...`). They recover on their own; nothing to do.
* **A portrait/vertical video loads but won't play right after posting** — this was a transient
  Discord proxy warm-up behavior (the same URLs play fine shortly after, confirmed across services).
  Direct URLs are the default again since round 5. If you ever confirm a *persistent* portrait
  breakage, set `PORTRAIT_PROXY = True` near the top of `testing area/twitter_v2_button_outside.py` /
  `testing area/twitter_v3.py` to route vertical videos through FxTwitter's embed proxy instead.
* **EmbedEZ suddenly errors after an update** — expected risk (their docs warn of breaking changes);
  the Actions log prints the raw API response to help adjust field names.
* **Combined feed returns "no RSS entries" / `429`** — Reddit's "loading takes a moment" HTML page or
  rate limit. The script rejects non-feed HTML automatically and falls back to per-subreddit fetches;
  adding `REDDIT_FEED_TOKEN` removes the rate-limit cause entirely.

---

## 📄 Final notes

* All engines are independent — mix and match freely (e.g. X on V3, Reddit on V1).
* Project docs include the [Privacy Policy](PRIVACY_POLICY.md), [Terms of Service](TERMS_OF_SERVICE.md),
  and [Python runtime policy](docs/PYTHON_RUNTIME.md). The release history lives in the
  [Changelog](#-changelog) section below.
* Be nice to the free services this project uses: follow the per-engine polling guidance (Reddit V3's
  practical cron floor is documented below), keep caches committed so nothing is fetched/posted twice,
  and consider donating to Nitter's author.
* All trademarks belong to their respective owners; this project is an unofficial, non-affiliated
  automation tool for personal servers.

---

## 🆕 Reddit V3 — rounds 42–45 (2026-10-01): delivery in one cron tick

Reddit posts used to reach Discord 5–10 minutes after they appeared. They
now arrive on the **first cron tick after the post is confirmed alive**,
with no loss of safety.

### The latency fix (round 42)

Every post used to wait a flat `POST_SETTLE_SECONDS` (300 s) so a mod or
AutoModerator had time to act. That wait was applied even to posts already
proven live. It is now evidence-based:

| Evidence this run | Wait before posting |
|---|---|
| Post present in `r/<sub>/new` | `POST_SETTLE_VERIFIED_SECONDS` = **60 s** |
| Listing unreadable, or post absent | `POST_SETTLE_SECONDS` = **300 s** (unchanged) |

A post visible in the public `/new` listing is by definition not filtered
and not in the mod queue — the two things the 300 s wait protected against.
60 s remains as an AutoModerator buffer. A confirmed post also skips the
mod-queue page fetches entirely.

**Result with a 5-minute cron:** average latency **7.5 min → ≈3.5 min**.
A post at 4:51 PM now lands at ~4:55 instead of ~5:00–5:03. The fast path
can never apply to a filtered, queued or removed post, because those are
absent from `/new` by definition.

### Fewer requests per run

* the Redlib post page was fetched up to **3×** per post → now **1×**
* the proxy chain ran **2×** per post → now **1×**
* a post confirmed in `/new` skips up to **9** mod-queue instance requests
* NSFW markers, duplicate identity and re-upload identity now ride on **one**
  batched Arctic Shift call

### NSFW gate — earlier, wider, fail-closed

The gate runs **before** any Discord message, embed, thumbnail or media
resolution — not just before sending. It rejects:

* posts marked `over_18`
* posts from communities marked `over18`
* crossposts whose **source post or source community** is NSFW

Missing, malformed or unfetchable metadata now **fails closed**: the post is
held as `nsfw_unknown` and re-checked, never posted on a guess. A blocked
post produces **no** Discord output of any kind — the log records only the
post id and the reason. `NSFW_FAIL_OPEN=1` restores the old behaviour.

**Round 45** keeps that strictness from costing speed: when the Arctic
archive has no record of a brand-new post, the marker is read off the live
Redlib post page instead of holding the post for another tick. The page is
one the run already fetches, so it costs no extra request; a **spoiler**
badge is never read as NSFW; an unreadable page still fails closed.

| Archive | Live page | Result |
|---|---|---|
| has record | not consulted | unchanged |
| no record | NSFW badge present | **blocked** |
| no record | renders, no badge | **delivered this tick** |
| no record | unreadable | held `nsfw_unknown` (fail closed) |

### Author re-upload gate (round 43)

Real case in `r/Genshin_Impact_Leaks`: post `1wukgrn` was deleted by its
author ~9 minutes in and re-uploaded as `1wukoah` — same title, same author,
new video file. The round-36 duplicate gate compares exact media URLs, and a
re-upload always gets a brand-new `v.redd.it` id, so it could not see this.

The gate now also compares a `sub|author|title` identity (case, punctuation,
whitespace and zero-width normalised, then matched **exactly** — no fuzzy
scoring) and skips a post already on Discord. An unknown author
(`[deleted]`) or an empty title yields no identity and the gate fails open.
It reuses the existing batched archive call, so it costs no extra request.

### Dead-post retraction — shipped disabled (rounds 43/44)

A delivered card whose Reddit post later dies can be rewritten in place as a
tombstone. It **edits, never deletes**: per Discord's
[Announcement Channel FAQ](https://support.discord.com/hc/en-us/articles/360032008192-Announcement-Channel-FAQ),
an edit updates the message in every following server while a delete leaves
a permanent `[Original Message Deleted]` note there — which matters because
this channel is autopublished. Two independent proofs are required, and the
post id stays in the dedup cache so a retraction can never cause a re-post.

It is **off by default** (`RETRACT_DEAD_POSTS=0`) because it costs extra
requests. When enabled it runs *after* the posting loop, so it adds no
latency, and only then is `wait=true` appended to the webhook call.

### New repository Variables (all optional)

| Variable | Default | Meaning |
|---|---|---|
| `POST_SETTLE_VERIFIED_SECONDS` | `60` | wait for a post confirmed in `/new` |
| `POST_SETTLE_SECONDS` | `300` | wait for an unverified post (unchanged) |
| `NSFW_FAIL_OPEN` | off | `1` restores pre-round-42 fail-open NSFW |
| `NSFW_REQUIRE_SUBREDDIT` | off | `1` also demands a readable community record |
| `NSFW_PAGE_FALLBACK` | on | `0` disables the live-page NSFW fallback |
| `REPOST_GATE` | on | `0` disables the author re-upload gate |
| `REPOST_WINDOW_SECONDS` | `86400` | how far back the re-upload comparison reaches |
| `RETRACT_DEAD_POSTS` | **off** | `1` enables tombstoning cards whose post died |
| `RETRACT_MODE` | `edit` | `edit` / `delete` / `off` |
| `RETRACT_WINDOW_SECONDS` | `21600` | how long a delivered card is watched |

Nothing needs to be set to get the speed improvement.

### Cron interval

The settle window is no longer the bottleneck — the cron is. With the
5-minute interval, latency is 1–6 min. Lowering it now pays off:

| Interval | Average latency |
|---|---|
| 5 min | ≈3.5 min |
| 3 min | ≈2.5 min |
| 2 min | ≈2.0 min |

Below ~2 minutes returns diminish (the 60 s AutoMod buffer becomes the
floor) while cache-commit churn and mirror rate-limiting both rise. If you
do lower it, set `APPROVAL_RECHECK_SECONDS` to match so held posts are
re-evaluated on every tick.

---

## 🗒 Changelog

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
  [consolidated tracking record](docs/REPOSITORY_TRACKING.md).

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
  remain current. See [Round 51 audit record](docs/ROUND_51.md).

* **2026-09-30 — Runtime, delivery, and source hardening.** All executable
  workflows now pin stable CPython **3.14.7**; CI installs, compiles, and smoke-tests
  that exact interpreter before merge. Cache persistence uses an explicit
  `HEAD:<branch>` push, bounded rebase retries (15 s / 30 s), and clear failure
  annotations so a lost dedup update cannot be silent. The X fallback chain now
  starts with the tracker-healthy RSS hosts, while the Reddit chains include the
  current official Redlib registry's token-free non-Cloudflare mirrors. The
  standalone `CHANGELOG.md` was retired; this in-README section is the single
  release history. See [Python runtime policy](docs/PYTHON_RUNTIME.md) for the
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

---
