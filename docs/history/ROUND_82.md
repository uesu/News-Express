# Round 82 — Reddit fleet expansion (19 → 23, Game-Express PR #63 parity, 2026-10-23)

## Trigger

* User: *"i asked first if there's new instances to add, that's all, no deletions but arrange — check and tests: https://github.com/uesu/Game-Express/pull/63"*
* Game-Express PR #63 `fabbe4c` (READY TO MERGE) expands Redlib fleet `17 → 22` (5 new hosts, demotes `privacyredirect.com` to Tier 3 after 403, adds `mitchross/redlib v2.3.6` parser + error-page/onion/flair hardening). News-Express is at 19-member R78 fleet — need parity with 0 deletions.

## Fleet change (19 → 23, 0 deletions — keep `nohost` + `kylrth` which Game excludes)

* **Tier 1 — Active healthy dual-path (9 hosts, 200 OK on /r/<sub>/new + /user/<acct> + /r/<sub>/comments/<id>/):**
  * `https://redlib.mint.lgbt` **NEW #0** — Redlib 0.36.0 `0baefabf` Shreddit build, deployed 2026-10-21, 100% 200 OK all three routes, direct TLS, no CF/Anubis, `SFW only = off`.
  * `https://reddit.idevicehacked.com` **promoted #1** — Redlib 0.40.0 `848f3013` (was #10), inline full gallery on /new (no second detail call), US direct, `Show NSFW = on`.
  * `https://redlib.catsarch.com`, `https://snoo.habedieeh.re` (v3.0.0 #592, 1080p CMAF), `https://redlib.miningtcup.me` (token-gated), `https://redlib.tiekoetter.com`, `https://redlib.nohost.network` **kept** (Game excludes but News keeps — 503 trap excluded in Game, here verified CMAF), `https://redlib-1.privadency.com`, `https://redlib-2.privadency.com`.

* **Tier 2 — Verified /new + /user/ listing-only (8 hosts, pre-#592/#599 on /comments/, REDDIT_LISTING_ONLY):**
  * `https://reddit.jeremyh.xyz` **NEW** — 0.31.0 redlib-instances#118, `https://redlib.jeikobu.net` **NEW** 0.36.0 `fca8b45c`, `https://redlib.vanillax.me` **NEW** `mitchross/redlib v2.3.6 abd6ba24` (standalone `<a class="post_title">` template) — all ahead of `red.artemislena.eu`, `rl.awy.one`, `redlib.kylrth.com` **kept** (Game excludes `kylrth` 301 CF, News keeps), `redlib.freedit.eu`, `redlib.utilibre.org`.

* **Tier 3 — Token + demoted/legacy tail (6 hosts, 0 hits while Tier 1 healthy):**
  * `https://www.reddit.com`, `https://old.reddit.com` (promoted to slot 0 with `REDDIT_FEED_TOKEN` — now Tier 3 tail, 0 waste when unauth 403 on Azure), `https://redlib.privacyredirect.com` **demoted** #4 → #19 after live 2026-10-23 `403 Forbidden ... at least 20 commits old` on both /new & /comments/, plus `redlib.privadency.com`, `safereddit.com`, `redlib.nadeko.net`.

* Traps never added: `rl.blitzw.in` honeypot, `red.arancia.click` parked, `redlib.jaydenha.uk` fake, `l.opnxng.com` alias, `redlib.kareem.one` Azure 403 — excluded.

## Savings / calls / requests — still good

* **No extra requests while healthy:** The retraction seatbelt (`_fetch_new_listing`) races all `REDDIT_RSS_INSTANCES` concurrently with an 8 s deadline and takes the **first usable answer** — Tier 3 tail is never hit while Tier 1 answers (0 cost). Same for `_fetch_post_rss` fallback (tries Tier 1 first, stops on first feed that validates `/comments/` links). Combined native RSS (`www.reddit.com/r/a+b+.../new.rss?limit=100&feed=…&user=…`) remains **1 request/run** covering all 6 subs; `REDDIT_FEED_TOKEN` memoization keeps `.json` fallback to ≤1 req/run (first new post only). Proxy chain (vxreddit → redditez → embeddit) unchanged, concurrent waves with `PROXY_WAVE_DELAY 0.5s`.
* **Eliminates 1 wasted request:** Demoting `privacyredirect.com` (always 403) from Tier 1 #4 removes 1 guaranteed-fail HTML fetch per cold batch on every run — same saving Game-Express PR #63 reports.

## Verification (tests only — no prod push yet)

* `python -m py_compile testing area/reddit_main_v3.py` + `python -m compileall -q .` → **OK**
* `python tests/test_smoke.py` → **SMOKE TEST: ALL PASS** (incl. `r82 23-member 3-tier order`, `r82 no-deletion` 19→23, `post-rss` now expects `mint.lgbt` head, `r78` historical preserved)
* `python tests/test_reddit_signals.py` → **ALL PASS** (96)
* `python tests/test_twitter_media.py` → **ALL PASS**
* Manual count: `len(REDDIT_RSS_INSTANCES) == 23`, `len(set)==23`, `mint.lgbt` head, `privacyredirect` index 19, traps absent.

## Deploy

* No `.github/workflows` edit — fleet is in `testing area/reddit_main_v3.py` only. Merge `arena/c5e99514-news-express` → manual upload `testing area/reddit_main_v3.py` + `tests/test_smoke.py` + docs to `7jkxmy9nvbc`/`wvkhabh2s22` (engine first per AGENTS.md). Previous Round 80 emoji fix (`_split_trailing_emoji80`) retained.
