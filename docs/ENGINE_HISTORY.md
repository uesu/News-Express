# Engine history — round-by-round notes (archived from the README)

> **Where this comes from:** until 2026-10-05 the main `README.md` carried
> every round's detailed behavior notes inline — ~1,450 lines of dated
> sections layered on top of each other. The 2026-10-05 README restructure
> moved all of them here, **verbatim and in their original order**, so the
> README can stay focused on the current shipped behavior.
>
> **Reading order tip:** each section is a snapshot of the engine *at that
> date* — later rounds supersede earlier ones. For the condensed,
> newest-first history see [`CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md)
> (rounds 1–62) and the changelog at the bottom of the
> [`README.md`](../README.md) (round 63+). Decision records for individual
> incidents live in the `ROUND_*.md` files in this folder.

## Contents

- [Part 1 — X (Twitter) monitor round notes](#part-1--x-twitter-monitor-round-notes)
  - 2026-09-11 card behaviors · round 4 · round 10 · round 11 (tweet-data
  fallback chain) · round 12 (nitter fleet resilience) · round 13 (repost
  attribution) · round 14 (miningtcup RSS token) · the twitter workflow YAML
  snapshot
- [Part 2 — Reddit monitor round notes](#part-2--reddit-monitor-round-notes)
  - round 12 (V3 differences) · round 13 (proxy media services) · round 14
  (card polishing) · round 17 (Arctic Shift backup) · round 23 (media must
  win) · round 24 (miningtcup redlib) · round 25 (most-complete-media-wins)
  · round 31 (.json probe) · round 32 (queued posts) · round 34 (dedup cache
  retention) · round 35 (NSFW gate) · round 33 (URL-labelled links) · the
  round-12 testing & verification procedure · the reddit workflow YAML
  snapshot · 2026-09-11 behaviors · V2 concerns · V1 fix · 2026-09-12 dead
  redlib/429 fixes · round 9 (combined RSS + feed token)
- [Part 3 — Round 63 & 64 delivery-pipeline details](#part-3--round-63--64-delivery-pipeline-details)

---

# Part 1 — X (Twitter) monitor round notes

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


---

### The workflow snapshot (`.github/workflows/twitter_monitor.yml`, as documented 2026-09)

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


---

# Part 2 — Reddit monitor round notes

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
  [Discohook](../README.md#-integrations) — now the Integrations section of
  the README). `DISCOHOOK_PREVIEW=0`
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
  listing, and proxy timing switches shown in [`.env.example`](../.env.example).
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
* **Docs added:** [`docs/DISCOHOOK.md`](DISCOHOOK.md) (Discohook =
  preview-only here, **fully optional**, safe to disable — and why it isn't
  relied on for posting) and [`docs/CI_SMOKE.md`](CI_SMOKE.md)
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
   | `not_live` / `pending approval` / `sources_down` (queued for approval, or a transient all-sources-down miss) / `media_wait` / `partial_gallery` | round 63: all re-checked on the **one uniform** `PENDING_RECHECK_SECONDS` interval (default 1800 s = 30 min, repo Variable). The mod-queue banner itself is still an explicit reason (`pending approval`) — a queued post is never mistaken for live even when a source renders the banner. |

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

> **Rounds 36–55 (settle window, duplicate-media gate, mod-queue detection,
> repost gate, page-identity check, listing health tuning) were removed in
> round 63 — see [the round-63 section](#-reddit-v3--round-63-2026-10-05-the-great-simplification)
> further down and [`docs/CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md)
> for their full implementation history.**

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


---

### The workflow snapshot (`.github/workflows/reddit_monitor.yml`, as documented 2026-09)

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


---

### Early Reddit fixes (2026-09-11 → 2026-09-13)

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


---

# Part 3 — Round 63 & 64 delivery-pipeline details

## 🆕 Reddit V3 — round 63 (2026-10-05): The Great Simplification

Earlier rounds (35–55) added a stack of timing and evidence gates — a settle
window, a mod-queue detector, a duplicate-media gate, a repost gate, and a
page-identity check — to work around moderation-queue and listing-timing
edge cases live-observed at the time. Round 63 removed all of them. The
Reddit engine now ships exactly **three protections**:

1. **The dedup cache** — a post's unique key (`<subreddit>_<post_id>`) is
   cached after a successful send; `MAX_CACHE_SIZE_PER_SUB` /
   `MAX_CACHE_SIZE_TOTAL` / `MAX_POSTS_PER_RUN` govern retention and
   per-run flood caps (round 34, unchanged).
2. **The fail-closed NSFW gate** — every new post is checked against
   Reddit's own NSFW markers (`over_18`, the `nsfw` thumbnail sentinel,
   subreddit `over18`, and crosspost-source flags) before any Discord
   work happens. Missing/unreadable metadata is held as `nsfw_unknown`
   and re-checked — it is never read as safe. When the archive has no
   record yet, the live Redlib post page's `<small class="nsfw">` badge
   is read instead (`NSFW_PAGE_FALLBACK`, round 45) so a brand-new post
   isn't held an extra cron tick just because the archive is lagging.
   `NSFW_FAIL_OPEN=1` restores the old fail-open behavior;
   `NSFW_REQUIRE_SUBREDDIT=1` also demands a readable community record.
   This gate is non-negotiable and is never removed or weakened.
3. **The opt-in retraction seatbelt** (shipped OFF) — when a previously
   delivered post is later confirmed dead (two independent proofs: absent
   from a `/new` listing that should still show it, AND a removal verdict
   from a live source), its Discord card can be rewritten in place as a
   tombstone (`RETRACT_MODE=edit`, default) or deleted
   (`RETRACT_MODE=delete`). The post's dedup-cache key is never touched,
   so a retraction can never cause a re-post. Enable with
   `RETRACT_DEAD_POSTS=1`; tune the window with `RETRACT_WINDOW_SECONDS`
   (default 21600 = 6 h).

Every other removed gate's full implementation history, the live incidents
that motivated each one, and the tuning tables that used to live here are
preserved verbatim in
[`docs/CHANGELOG_ARCHIVE.md`](CHANGELOG_ARCHIVE.md).

**What this means for latency:** a new post now delivers on the **first
cron tick after it's confirmed not-NSFW** — there is no longer a settle
window or queue-evidence wait layered on top. Latency is simply your cron
interval (see [Step 4](../README.md#step-4--reliable-10-minute-automation-external-trigger)
of the README).

**Rollback:** none of the removed gates can be re-enabled via a Variable —
they no longer exist in the code. To restore old behavior, check out a
pre-round-63 commit of `testing area/reddit_main_v3.py` from Git history.

---

## 🆕 Reddit V3 — round 64 (2026-10-05): Pristine Listing Protocol

**How a post gets delivered:** a new Reddit post is only sent to Discord once
its own age clears a flat, stateless `FRESH_HOLD_SECONDS` floor (default
30 s) **and** a fresh, cache-busted read of the subreddit's `/new` listing
proves it's actually live right now. Not listed yet? It's skipped for this
tick only — never blocked, never cached — and posts the instant a later
tick finds it there. The three round-63 protections (dedup, fail-closed
NSFW, retraction seatbelt) are unchanged and still run exactly as before.

1. **Stateless 30 s fresh hold (`FRESH_HOLD_SECONDS`, default 30).** Age is
   computed straight from the post's own timestamp — no first-seen
   tracking, no pending entry, no inference of any kind. `FRESH_HOLD_SECONDS=60`
   is an extra-cautious floor (covers slower AutoModerator passes) and
   `FRESH_HOLD_SECONDS=0` turns it off. At any cron interval of 2 minutes or
   more, either value costs the post at most one tick of extra latency.
2. **Pristine listing confirmation (`LISTING_CONFIRM`, default 1).** Every
   tick, each monitored subreddit's `/new` listing is fetched with a unique
   `_fresh=<unix ms>` cache-buster on every single request plus
   `Cache-Control: no-cache, no-store` / `Pragma: no-cache` headers, so no
   CDN or proxy can hand back a stale page — and the result is never reused
   across runs. A candidate present in that listing proceeds; absent, it's
   skipped this tick and re-checked next tick (logged, never cached). If the
   candidate is older than the listing's own oldest entry (scrolled past
   `limit=100`), confirmation is inapplicable and it falls straight through
   to normal delivery. If no listing source is readable at all this tick,
   that's an **outage**, never read as absence — every new candidate for
   that subreddit is skipped and retried next tick.
3. **No AutoModerator or sticky-comment detection of any kind** — no phrase
   matching, no inference, no tracker state. `LISTING_CONFIRM=0` restores
   round-63 delivery; pair it with `FRESH_HOLD_SECONDS=0` for a full,
   byte-for-byte return to pre-round-64 behavior.

**Precedence:** dedup skip → `FRESH_HOLD_SECONDS` floor → pristine listing
confirmation → the fail-closed NSFW gate (unchanged, still fail-closed) →
deliver. The retraction seatbelt is unaffected.

---

