# Privacy Policy

**Effective date:** October 17, 2026
**Applies to:** the *News Express* / *Citlali News* X (Twitter) + Reddit → Discord monitor
("the Service"), an open-source, self-hosted automation tool.

---

## 1. Overview

The Service is a set of Python scripts that run on **your own GitHub repository** (GitHub Actions)
and post new public X/Twitter and Reddit items into **your own Discord channels** via Discord
webhooks. There is no hosted bot account, no gateway connection, no dashboard, and no central server
operated by the author.

**Short version:** the Service does not collect Discord member data, operator analytics, or account credentials. It necessarily processes **public post content** (which a public poster may choose to include personal information in), stores small delivery-state records, and sends rendered public content to the Discord webhooks you configure.

---

## 2. Data the Service Processes

| Data | Where it lives | Why | Shared with anyone? |
|---|---|---|---|
| Delivery-state records: post/tweet IDs (e.g. `TYPEII_EN_2098063866303504597`), pending reasons, and proxy health | `posted_tweets.json`, `posted_reddit.json`, `pending_reddit.json`, and `proxy_health.json` **inside your own repository**, committed by `github-actions[bot]` | Deduplication, safe re-checks, and proxy fallback health | GitHub and anyone who can access your repository; a public repository makes these records public. They do not contain Discord member data or webhook URLs. |
| Optional retraction records: Reddit post path, Discord message ID, delivery/publish timestamps, and the rendered card payload | `posted_messages.json` **inside your own repository**, created only when `RETRACT_DEAD_POSTS=1` and committed by `github-actions[bot]` | Lets the optional dead-post retraction pass edit or delete the exact Discord message; records are pruned after `RETRACT_WINDOW_SECONDS` and marked retracted records are removed | GitHub and anyone who can access your repository; a public repository makes these records public. The payload is the same public card sent to Discord and does not contain member data or webhook URLs. |
| Webhook URLs, API keys & optional feed/RSS tokens | GitHub **encrypted repository secrets** in *your* repository | Authentication to Discord, EmbedEZ, Reddit, or a token-gated mirror | GitHub stores the secrets. A value is sent only to its intended service when needed (for example, a webhook to Discord, a Reddit feed token to Reddit, or the Nitter token to miningtcup); the Service must not intentionally publish it. Output redaction and GitHub masking are safeguards, not guarantees; review logs before sharing them. |
| Public post content (titles, text, author names/handles, media URLs, stats) | Processed **in memory** during a run; rendered content is retained by the Discord channel under your control | Rendering the Discord message | Discord receives the rendered public content through the webhook(s) you configure. Relevant source services receive the public URL/account/subreddit requested. |

No analytics, no tracking, no cookies, no separate database, no telemetry, and no advertising are added by this project.

---

## 3. Data the Service Does NOT Collect

* Discord user information (usernames, IDs, messages of server members) — the Service cannot read
  any of it; webhooks are **one-way, post-only**.
* X/Twitter or Reddit account credentials — only **public** posts are fetched via public RSS/API
  endpoints; no login is used or stored. (The optional Reddit *feed token* is a public-read
  credential for RSS only — it grants no access to your account, DMs, or profile, and can be
  regenerated at any time.)
* IP addresses or device information of anyone.
* Any payment information.

---

## 4. Third-Party Services

When the Service runs, it makes outbound requests to the following third parties. Their own privacy
policies apply to whatever they can technically observe (typically just the requesting IP and the
public URL being looked up):

| Service | Purpose | Their policy |
|---|---|---|
| **GitHub Actions** | Hosts and runs the scripts | https://docs.github.com/en/site-policy/privacy-policies |
| **Discord (webhooks)** | Delivers the generated messages; when optional dead-post retraction is enabled, the webhook response supplies a message ID and the monitor may later edit or delete that public card after two removal signals | https://discord.com/privacy |
| **Nitter mirrors** | Public RSS feeds for X/Twitter | per-instance |
| **Redlib** | Reddit RSS fallback mirrors and (Reddit V3) best-effort **post-page** fetches for multi-photo galleries, liveness checks, and on-demand test posts. This includes community-operated instances such as catsarch, nadeko, privadency, miningtcup, safereddit, artemislena, and privacyredirect; availability and operator policies vary. The pristine listing confirmation (round 64) and the optional dead-post retraction seatbelt (round 44) read public `/new` listings — including the HTML `/r/<subreddit>/new?limit=100` fallback — to determine whether a public post is visible; that URL carries only the public subreddit name, a cache-busting timestamp, and, for the token-gated miningtcup mirror, that mirror's own access token. The same instances are probed in parallel where applicable; anti-bot challenges can make a request fail fast. | per-instance |
| **FxTwitter / FxEmbed API** (incl. sister host **api.fixupx.com**) | **Primary** tweet metadata, media, translation; if the primary host can't answer, the same-engine fixupx host is tried (round 11) | https://fxtwitter.com |
| **video.twimg.com / x.com (X CDN & post pages)** | HTTP HEAD probes of public video file sizes (X V2/V3 "smart video" check) and OpenGraph image lookups on public post pages — only meta tags are read, no content is downloaded | https://x.com |
| **gif.fxtwitter.com** | 1st of the GIF converter chain (round 11): one HEAD probe per X GIF to check the animated WebP rendition exists before using it | https://fxtwitter.com |
| **api.vxtwitter.com** (BetterTwitFix) | 3rd fallback for tweet metadata/media (round 11) — public tweet data only; its direct `video.twimg.com` media URLs are what the bot then probes | https://vxtwitter.com |
| **gifconvert.vxtwitter.com** | 2nd/3rd of the GIF converter chain (round 11): one HEAD probe per X GIF (`.webp`, then `.gif`, with a browser Referer) to check a converted animated rendition exists before Discord uses it | https://vxtwitter.com |
| **fastgif-production.up.railway.app** | Last probe of the GIF chain (round 11; offline since 2026-09-17 — retained so it is used automatically again if it returns): one HEAD probe per X GIF to check the converted animated GIF exists; if it answers, Discord fetches that converted GIF when rendering the post. Independent third-party service, unaffiliated with this project or FxTwitter | https://railway.app |
| **EmbedEZ API** | Reddit V2: Reddit post metadata, media. Reddit V3 (round 13, "redditez" proxy-media source): per-post keyless `search` API lookup + one bot embed-page og: tag read for public post media/title/stats, plus one warm-up probe per run. X V3 (round 11, **last-resort only**): tweet metadata via the keyless search API + one bot-page og: tag read per tweet when fxtwitter/fixupx/vxtwitter all fail; the media URLs are then fetched by **Discord's servers** (animated WebP for GIFs), and any embedded promo/ad line is stripped before posting | https://embedez.com |
| **Arctic Shift** (arctic-shift.photon-reddit.com) | Reddit V3 archive: post-lookup JSON for crosspost originals, and — only for subreddits that returned no new RSS posts — one `/api/posts/search` per missing subreddit (public post data only, 48-hour window); soft-fails back to the RSS path on any error | https://arctic-shift.photon-reddit.com |
| **redditez.com** (Reddit V1 default mirror) | No direct contact: the Service only *constructs* the mirror link from the public post path; **Discord's servers** fetch that URL to render the unfurled embed | https://www.redditez.com |
| **embeddit.deltandy.me / vxreddit.com** | Reddit V1 (only if you switch `REDDIT_MIRROR`): link construction only — Discord fetches the mirror when rendering. Reddit V3 (round 13, proxy-media sources): direct per-post fetches of **public post data only** — vxreddit's bot embed-page og: tags, and Embeddit's Mastodon-style status JSON (or, if the instance migrates to the Embeddit rewrite, its Component-Embed bot page at the same public post path — round 54); both also get one warm-up probe per run. Only the public subreddit/post-id path is sent. Both are independent community projects, unaffiliated with this project | https://embeddit.deltandy.me |
| **reddit.com / old.reddit.com** | Public subreddit RSS — all tracked subreddits in **one combined feed request per run** (`/r/a+b+c/new.rss?limit=100`), plus the per-subreddit `/new` listing — attempted as RSS (`/new.rss?limit=100`) and as HTML (`/new?limit=100`), first usable answer wins — used by Reddit V3's pristine listing confirmation (round 64) and optional dead-post retraction seatbelt (round 44). The combined feed and the RSS listing may carry your personal feed token, sent only to Reddit; these reads use public entry IDs and `pubDate` values, not account data. Reddit V3 also makes per-post `.json` lookups when enabled (OAuth app token when an app is configured, or the feed token as a best-effort workaround — round 31: only when an app exists or `REDDIT_JSON_PROBE=force`) — public post data + public top-level comments only | https://www.reddit.com/policies/privacy-policy |
| **i.redd.it / preview.redd.it / v.redd.it** (Reddit's own CDNs) | V3 media verification only: one short HTTP range probe per candidate media file (images/videos) to check it exists and is playable; the signed `packaged-media.redd.it` masters (which expire in hours) are never used | https://www.reddit.com/policies/privacy-policy |
| **proxy.embedez.com / vxreddit.com** | V3 video fallback only, and only when Reddit's own `v.redd.it` DASH files are unavailable: the *public video file URL* (no account data) is passed so they can return a muxed (video+audio) mp4 for the card | https://embedez.com / per-instance |
| **seaof.glass** (quartz) | Only if you enable `YOUTUBE_MEDIA_EMBED=1` (default off): one range probe per YouTube video id to see if a playable mp4 exists — the video id only | per-service |
| **i.ytimg.com** (YouTube thumbnails) | One probe per YouTube post to pick the best available thumbnail (maxres/hq/mq) | https://policies.google.com/privacy |
| **discohook.app** (optional, on by default) | Per-card **share-link preview** of the public card payload only (POST `/api/v1/share`, keyless). **No `targets` are sent, so your webhook URL and any tokens never leave the repository.** Share links are public for their 7-day TTL; disable with `DISCOHOOK_PREVIEW=0` | https://discohook.app |
| **GitHub (Dependabot, optional)** | If you keep `.github/dependabot.yml`, GitHub's built-in Dependabot opens **pull requests only** (never pushes to `main`); it sees your dependency files, nothing else — see `docs/DEPENDABOT.md` | https://docs.github.com/en/site-policy/privacy-policies |
| **cron-job.org** (optional) | External schedule trigger | https://cron-job.org/en/privacy/ |

The Service never reads or sends these third parties Discord server-member data or private Discord content. It sends only the public post/account/subreddit identifiers needed to fetch a source; Discord receives the rendered public post content through the webhook you configured.

---

## 5. Data Retention

* Delivery-state files (`posted_tweets.json`, `posted_reddit.json`, `pending_reddit.json`, and
  `proxy_health.json`) live in your repository until you delete them. Post-ID caches retain the
  newest 250 keys per monitored source by default, with a 10,000-key global backstop.
* `posted_messages.json` is conditional: it is created only when dead-post retraction is enabled,
  retains undelivered/retraction candidates for `RETRACT_WINDOW_SECONDS` (default six hours),
  and is pruned after each run. The default configuration does not create this file.
* Rendered messages and public content are retained by Discord under the retention/moderation
  settings of the server you operate.
* GitHub retains workflow logs and step summaries according to its applicable
  access and retention settings. They can include public source references,
  operational outcomes, selected-feed counts and elapsed time. The existing summary
  output adds no separate database, JSON report or analytics endpoint. Redaction
  is best effort; operators should review output before publishing it.
* The project adds no other database or telemetry store.

---

## 6. Your Responsibilities & Rights

Because you operate your own instance, **you** are the data controller for it. You may inspect,
modify, or delete every byte it holds (the four always-present workflow-managed JSON state files and
the conditional `posted_messages.json` file) at any time. Server members who want messages removed can
ask you (or any admin with *Manage Messages*) to delete them from Discord.

---

## 7. Children's Privacy

The Service is not directed at children under 13 and does not collect Discord member data. Like any
public-content relay, it may process public material that a source poster chose to publish; operators
must use the Service only where permitted by applicable law and platform rules.

---

## 8. Changes to this Policy

Changes are committed to this repository's `PRIVACY_POLICY.md` with an updated effective date.
Material changes will also be announced in the project's Discord server.

---

## 9. Contact

* GitHub: open an issue on this repository
* Discord: https://discord.gg/HyrVP9wRXu
* Support/dev: https://ko-fi.com/jieunlatte
