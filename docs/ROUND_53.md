# Round 53 — Embeddit incident root cause: empty string Variables override string defaults (2026-10-01)

## Incident

Production run 2026-10-01 23:13 UTC (Reddit monitor, live repo) logged, for
**every** post that reached the proxy chain:

```
[Genshin_Impact_Leaks_1wvcysk] embeddit error: /api/v1/statuses/4f1y494d453t1y2m1y454448491y291y3x3s1y2m1y2d4b4a3r4d483z1y291y423t473v3t1y2m4947403t4h
[Genshin_Impact_Leaks_1wvcysk] embeddit had no usable data.
```

and, on every run:

```
PROXY_WARMUP_POST '' is invalid — use <subreddit>/<post_id>. Warm-up skipped.
```

The run itself stayed healthy — vxreddit supplied the media, the card posted,
the cache committed. But Embeddit was silently dead as a source on every run,
and the warm-up never refreshed `proxy_health.json`.

## Root cause — NOT the Embeddit instance

The workflow wires the options as `EMBEDDIT_INSTANCE: ${{ vars.EMBEDDIT_INSTANCE }}`
and `PROXY_WARMUP_POST: ${{ vars.PROXY_WARMUP_POST }}`. With no repository
Variable set, GitHub exports them as **empty strings**, and
`os.getenv(name, default)` treats an empty string as a real value — the
documented default never applied. So:

* `EMBEDDIT_BASE` became `""` and every request targeted the **relative** url
  `/api/v1/statuses/<id>`. aiohttp raises `InvalidUrlClientError` before a
  socket is ever opened, and `str(e)` for that exception is *just the url* —
  which is exactly the cryptic production log line. Reproduced 1:1 offline;
  the same status id returns valid post JSON when prefixed with the default
  host (verified live 2026-10-01), so the hosted instance was fine.
* `WARMUP_POST_ID` became `""` and the warm-up skipped itself every run.

This is the same bug class round 36 / round 49b fixed for *numeric* reads
(`_env_int`/`_env_float`) — the two *string* reads were missed.

## Changes

### `testing area/reddit_proxy.py`

1. **`_env_str()`** — the string counterpart of `_env_int`/`_env_float`:
   unset, empty and blank all mean the documented default. Used for
   `EMBEDDIT_INSTANCE` and `PROXY_WARMUP_POST`.
2. **`_normalize_instance()`** — an operator-supplied instance value is
   normalized to a usable absolute base URL: bare hosts gain `https://`
   (the `REDDIT_MIRROR` Variable is stored bare in this repo, so a bare host
   must work), trailing slashes are dropped, and anything that is not a
   usable http(s) host (empty, `ftp://…`, `https://`, embedded spaces) falls
   back to the default with one clear warning. `EMBEDDIT_BASE` can therefore
   never be relative again.
3. **Warm-up never skips** — a malformed `PROXY_WARMUP_POST` now logs the
   warning and probes the built-in default post instead of abandoning the
   warm-up, so `proxy_health.json` stays fresh and dead services keep being
   skipped per run.
4. **Diagnosable error line** — the embeddit error log now includes the
   exception **class** and the instance **host**:
   `embeddit error (InvalidUrlClientError) for embeddit.deltandy.me: …`.
   The 2026-10-01 incident looked like a remote failure precisely because
   `str(e)` alone printed only the url.
5. **Run-scoped route-gone detection (Embeddit PR #2 readiness)** —
   DeltAndy123/Embeddit PR #2 is a full rewrite (Bun + Hono, Discord
   Component Embeds instead of the Mastodon spoof). If/when the hosted
   instance ships it, `/api/v1/statuses/<id>` stops existing. A missing
   route is permanent for the run, unlike a per-post miss: the live
   instance answers an unknown/dead post with a Cloudflare **502**
   (verified 2026-10-01), never 404 — so `404/410/501`, or a 200 that is
   not JSON, can only mean "this instance does not serve the Mastodon API".
   On the first such response embeddit is dropped from the dispatch order
   for the **rest of the run** after one explanatory warning (never to an
   empty order — the last remaining service is still asked, same rule as
   the share-link drop). Timeouts, 429, 5xx and parse misses stay per-post
   misses, exactly as before. vxreddit/redditez/native media are unaffected
   either way — the chain design already proved itself in this incident.

### `testing area/reddit_main_v3.py` / `testing area/twitter_v3.py`

`SUBREDDITS` / `ACCOUNTS` are wired as **secrets** in the workflows — the
same empty-string injection applies when a secret is unset. Both now treat
empty as "not configured" and keep their documented default lists instead of
silently monitoring zero feeds.

## Not changed, deliberately

* `DISCORD_WEBHOOK_URL`, `REDDIT_FEED_TOKEN`, `NITTER_RSS_TOKEN`,
  `TEST_POST_ID`, `NSFW_ALLOWLIST`, … — empty already means "feature off /
  not configured" for these; that behavior is correct and untouched.
* The proxy chain order, waves, grace windows and tie-breaks (rounds 49/50)
  are untouched — this round only fixes how the chain's *configuration* is
  read and how an instance-level outage is classified.
* No workflow changes: the `reddit_monitor.yml` comment ("each Python module
  restores its documented default for empty values") is now actually true
  for the string Variables as well.

## Operator notes (live repo)

* No action required: with `EMBEDDIT_INSTANCE` unset (or set to the empty
  string) the default `https://embeddit.deltandy.me` now applies.
* To pin an instance explicitly, either form works as a repository
  Variable: `embeddit.deltandy.me` or `https://embeddit.deltandy.me`.
* `PROXY_WARMUP_POST` may stay unset; the built-in warm-up post applies.

## Regression coverage

`tests/test_smoke.py` (offline, no network, no secrets) round 53 block:

* empty `EMBEDDIT_INSTANCE` → the default absolute base URL;
* empty `PROXY_WARMUP_POST` → the default warm-up post;
* empty `SUBREDDITS` / `ACCOUNTS` → the default lists (6 subs / 5 accounts);
* `_normalize_instance` table: bare host, trailing slash, full URL,
  `http://localhost:3000`, and the garbage inputs that must fall back;
* 404-marking drops embeddit from `proxy_services_for()` for the run,
  never below one service, and `_fetch_embeddit` short-circuits without
  touching the network; reset restores the full order;
* an invalid `PROXY_WARMUP_POST` still probes the default post and still
  writes the health file;
* a source guard: no bare `os.getenv("EMBEDDIT_INSTANCE", …)` /
  `os.getenv("PROXY_WARMUP_POST", …)` may reappear.
