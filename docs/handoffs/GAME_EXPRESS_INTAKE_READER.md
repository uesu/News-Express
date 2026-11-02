# Hand-off — Game-Express: the Devvit relay as the primary Reddit listing (intake reader)

**For:** the `uesu/Game-Express` maintainer session (dev repo → prod `uesu/8mqzv4k2n7c` via its
own `sync_prod.yml`). **From:** News-Express rounds 101–107 (2026-11-02). **Base:** Game-Express
`main` @ `71202ee4` (PR #140) — regenerated on that exact commit on 2026-11-02 13:30Z: `git am` applies with **no conflicts** (changelog index, changelog order and the PROD-REPO-SETUP file count 47/49 are already right for #140). **Scope:** Game-Express's needs only — the Reddit *listing* source;
no card, schedule, codes, beta or news logic is touched.

The complete, tested patch is next to this file:
[`game-express-intake-reader.patch`](game-express-intake-reader.patch) (`git am`-able, 19 files). Everything below is a description of what that patch does and how to verify it.

## 1. What it does

`RedditClient._gather_listing()` asks a new `IntakeReader` first. The reader fetches the private
Discord **intake channel** once per run (bot token, REST `GET /channels/<id>/messages`,
newest-first, ≤ 8 × 100 messages, 6 h window), parses the *Gaming Express* relay's fenced-JSON
records and serves `r/<sub>` / `u/<account>` listings from them in the exact dict shape
`parse_reddit_json()` / `parse_redlib_html()` produce. `items()`, `program_post()`,
`community_codes()`, the official rule (`_is_official_subreddit_post`, flair ∪ distinguished ∪
verified author) and the muxed-video proxy chain are unchanged.

Rules, identical to the News-Express reader:

| Situation | Result |
|---|---|
| secret `DISCORD_BOT_TOKEN` + Variable `INTAKE_CHANNEL_ID` set, newest relay record ≤ `INTAKE_STALE_SECONDS` (1800 s), target has ≥ 1 record in the window | relay **is** the listing → **0** redlib / reddit.com requests for that target |
| target has no record in the window (dormant `u/ZZZ_Official`, `u/AnantaOfficial`) | old chain for that target, exactly as before |
| unset / HTTP 401·403·404·429 / stale / empty / messages with empty `content` (Message Content Intent missing) | old chain + one step-summary line `📡 reddit intake: relay <status> (<why>) — redlib/reddit.com chain used` |
| `INTAKE_READER=shadow` | reads and reports, old chain decides |
| `INTAKE_READER=off` | never reads |

Freshness is measured on **relay records only** — the owner shares the channel (`#modlogs`) with
other bots, and a fresh Wick/SassGuard line must never vouch for a silent relay. Paging is
newest-first (`before=`), so a busy channel can only shorten the look-back, never hide fresh
records. `removed` records count as a live relay but never become entries. Relay entries carry
`relay: True` and `body_truncated` (bodies above the relay's message budget arrive cut;
`resolve_post()` fills them as for any empty-text entry).

Game-Express's zero-waste rule is kept: Reddit is still consulted only when X or a primary API
missed; when it is, a served target costs nothing.

### Relay 0.0.7 — the relay is the complete source (round 103)

- **`record.json`**: every record message also carries the untrimmed record (full body, every
  media URL, the crosspost parent as a nested record). The reader fetches it from
  `cdn.discordapp.com` (`source="intake-cdn"`, no token) **only** for cut records
  (`bodyTruncated` / `mediaTruncated`) and crossposts without a parent permalink, ≤ 10 per run;
  a failed read leaves the inline record (and `resolve_post()` fills the body as before).
- **`v: 2` update messages**: the relay re-checks delivered posts at ~10 min / 30 min / 2 h / 6 h.
  The latest look per id decides: removed or deleted ⇒ not listed; a post first relayed as
  filtered and later shown live ⇒ listed. Update messages count as relay liveness (a quiet relay
  is `empty (relay alive …)`, old chain runs, nothing to serve anyway).
- **Edits**: an edited body arrives as a re-sent record (`revision` ≥ 2); newest message per id
  wins, entries carry `edited`.
- Entries gain `crosspost_url` (parent permalink) and a crosspost shows its parent's media.
- Step summary: `… newest S s, N re-checked, N completed from record.json; served …`.

### Relay 0.0.8 — 1:1 with the old chain (round 104)

- **Re-check stages** are now ~5 min / 30 min / 2 h / 6 h / 24 h. A post first relayed as
  filtered/removed and later shown live (approval) is **re-sent complete** (`resent: "approved"`),
  so the reader never depends on a record that may have left its 6 h window.
- **`relay_complete`** on every entry (nothing cut, parent named). `items()` and
  `program_post()` never call `resolve_post()` for such an entry — an empty `text` is a title-only
  post, not a missing body — so a relay-served game costs **zero** redlib / reddit.com requests
  even for title-only posts and for the Special-Program backup lookup. Cut records (CDN read
  failed) keep the old-chain fill-in exactly as before.

### Round 107 cross-check — a post approved from the mod queue hours later

Live 1xlrj90 (2026-11-02): created 07:31Z, held in the mod queue, approved ~12:35Z, listed by
the relay at 12:36Z. In News-Express an old-chain archive hold (`removal_notice`) suppressed the
relay record until the round-107 restore rule. **Game-Express has no equivalent defect and needs
no port of that rule:** its Reddit source keeps no hold memory (a removed post is simply not an
item), `items()` reads `LOOKBACK_HOURS` (72 h) back, and the reader lists any record whose relay
message is inside its window — so the same record is a plain new item with `published_ts` = the
Reddit creation time. The patch adds the test block
`test_round107_post_approved_from_the_mod_queue_hours_later_is_a_plain_new_item` (8 blocks now)
and one changelog sentence; it also pins the memory-free property (`removal_notice` /
`pending_reddit` must not appear in `gamexpress/sources/reddit.py`).

## 2. Files in the patch

| File | Change |
|---|---|
| `gamexpress/sources/reddit_intake.py` | **new** — `parse_intake_record`, `parse_intake_update`, `attachment_url`, `needs_full_record`, `apply_full_record`, `record_to_entry`, `IntakeReader` (`fetch`, `listing`, `summary_line`) |
| `gamexpress/sources/reddit.py` | `RedditClient.__init__` creates `self.intake`; `_gather_listing()` returns the relay listing when available (6 lines); `items()` / `program_post()` skip `resolve_post()` for `relay_complete` entries (round 104) |
| `gamexpress/config.py` | `Settings.intake_reader / discord_bot_token / intake_channel_id / intake_stale_seconds / intake_lookback_seconds` + env wiring (`GE_SECRETS_JSON` / `GE_VARS_JSON` already carry every secret/variable → **no workflow env edit**) |
| `gamexpress/runner.py` | one `ctx.report` line from `reddit.intake.summary_line()` |
| `gamexpress/__main__.py` | `validate` prints `Reddit intake=… bot_token=set/— channel_id=set/—` |
| `tests/test_reddit_intake.py` | **new** — real first-day records (gallery + `\_` escapes, video + poster + truncated body, inline images, YouTube link, gif, official flair), every status, paging, shared-channel noise, `items()` for a publisher-account game and for Wuthering Waves, shadow/stale/unconfigured; 0.0.7 updates, `record.json` completion + bounds, edits, approvals; 0.0.8 `relay_complete`, no-resolve `items()` / `program_post()`; round-107 mod-queue approval cross-check (8 blocks) |
| `tests/test_smoke.py` | policy effective date `November 2, 2026` |
| `.github/workflows/ci.yml`, `python_version_bump.yml` | run `tests/test_reddit_intake.py` (the "every test file is a gate" guard requires it) |
| `.env.example`, `README.md`, `docs/CONFIGURATION.md`, `docs/SOURCES.md`, `docs/PROD-REPO-SETUP.md` (file count 46 → 47 as of #140), `docs/changelog/CHANGELOG.md` + `README.md` index, `PRIVACY_POLICY.md`, `TERMS_OF_SERVICE.md`, `AGENTS.md` | documentation of the reader, the two settings, the bot's read-only scope |

### The wiring diff (the new module and tests are in the patch file)

```diff
diff --git a/gamexpress/__main__.py b/gamexpress/__main__.py
index 4f77ee1..52bf61a 100644
--- a/gamexpress/__main__.py
+++ b/gamexpress/__main__.py
@@ -389,6 +389,10 @@ def cmd_validate(_args) -> int:
     print(f"Reddit={'on' if settings.reddit_enabled else 'off'} "
           f"| reddit instances={len(settings.reddit_instances)} | proxies={len(settings.reddit_proxies)} "
           f"| feed_token={'set' if feed_q else ('invalid' if settings.reddit_token else '—')}")
+    print(f"Reddit intake={settings.intake_reader} "
+          f"| bot_token={'set' if settings.discord_bot_token else '—'} "
+          f"| channel_id={'set' if settings.intake_channel_id else '—'} "
+          f"| stale={settings.intake_stale_seconds}s | lookback={settings.intake_lookback_seconds}s")
     print(f"news={'on' if 'news' in settings.features else 'off'} | news games={','.join(sorted(settings.news_games))} "
           f"| article count cap=none "
           f"| timestamps={'on' if settings.news_timestamps else 'off'} "
diff --git a/gamexpress/config.py b/gamexpress/config.py
index d7be933..ec45d89 100644
--- a/gamexpress/config.py
+++ b/gamexpress/config.py
@@ -512,6 +512,13 @@ class Settings:
     reddit_instances: list[str] = field(default_factory=lambda: list(DEFAULT_REDDIT))
     reddit_proxies: list[str] = field(default_factory=lambda: list(DEFAULT_REDDIT_PROXIES))
     reddit_token: str = ""
+    # Devvit relay intake reader (2026-11-02): the primary Reddit listing; the redlib /
+    # reddit.com chain above stays as the automatic fallback. Same names as News-Express.
+    intake_reader: str = "primary"      # primary | shadow | off
+    discord_bot_token: str = ""          # secret DISCORD_BOT_TOKEN (read-only bot in the server)
+    intake_channel_id: str = ""          # Variable INTAKE_CHANNEL_ID (the intake channel)
+    intake_stale_seconds: int = 1800
+    intake_lookback_seconds: int = 21600
 
     news_enabled: bool = False
     news_games: set[str] = field(default_factory=set)
@@ -754,6 +761,12 @@ def load_settings(env: Mapping[str, str] | None = None) -> Settings:
         reddit_instances=reddit or list(DEFAULT_REDDIT),
         reddit_proxies=reddit_proxies or list(DEFAULT_REDDIT_PROXIES),
         reddit_token=_env(env, "REDDIT_FEED_TOKEN"),
+        intake_reader=(_env(env, "INTAKE_READER").lower() if _env(env, "INTAKE_READER").lower()
+                       in ("primary", "shadow", "off") else "primary"),
+        discord_bot_token=_env(env, "DISCORD_BOT_TOKEN"),
+        intake_channel_id=re.sub(r"\D", "", _env(env, "INTAKE_CHANNEL_ID")),
+        intake_stale_seconds=max(60, _int(env, "INTAKE_STALE_SECONDS", 1800)),
+        intake_lookback_seconds=max(600, _int(env, "INTAKE_LOOKBACK_SECONDS", 21600)),
         show_legend=_bool(env, "SHOW_LEGEND", True),
         repost=_env(env, "REPOST").replace(" ", "").lower(),
         http_timeout=_int(env, "HTTP_TIMEOUT", 20),
diff --git a/gamexpress/runner.py b/gamexpress/runner.py
index 910c749..65dfc1b 100644
--- a/gamexpress/runner.py
+++ b/gamexpress/runner.py
@@ -367,6 +367,9 @@ async def run_once(settings: Settings, games_all: dict[str, Game] | None = None,
                         record["paused"] = True
             if not features:
                 ctx.report.append("⏸️ no active features this run (ENABLED_FEATURES=none or passive standby)")
+            intake_line = reddit.intake.summary_line()
+            if intake_line:
+                ctx.report.append(intake_line)
         except Exception as exc:  # noqa: BLE001 — guarantee persistence & step summary on unexpected abort
             log.exception("unexpected failure during run_once orchestration")
             ctx.errors.append(f"orchestration failed: {_summary_text(exc)}")
diff --git a/gamexpress/sources/reddit.py b/gamexpress/sources/reddit.py
index 31b101c..57bceda 100644
--- a/gamexpress/sources/reddit.py
+++ b/gamexpress/sources/reddit.py
@@ -1008,6 +1008,10 @@ class RedditClient:
         self._post_cache: dict[str, dict | None] = {}
         self._json_feed_blocked: bool = False
         self.reachable: set[str] = set()
+        from .reddit_intake import IntakeReader  # local import: the reader imports this module's regexes
+
+        # Devvit relay intake (2026-11-02): consulted first by `_gather_listing`; `None` = old chain.
+        self.intake = IntakeReader(fetcher, settings)
 
     async def _get_text(self, url: str, **kwargs) -> str | None:
         fn = getattr(self.fetcher, "get_text", None)
@@ -1117,6 +1121,11 @@ class RedditClient:
         return good
 
     async def _gather_listing(self, kind: str, target: str) -> list[dict] | None:
+        # Devvit relay first: a healthy relay with records for this target IS the listing
+        # (0 redlib / reddit.com requests); anything else falls through unchanged.
+        relay = await self.intake.listing(kind, target)
+        if relay is not None:
+            return relay
         merged: dict[str, dict] = {}
         working = 0
         fleet = self._eligible_instances(for_post_detail=False, kind=kind)
@@ -1492,7 +1501,11 @@ class RedditClient:
                 links = list(e.get("links") or [])
                 combined = f"{e.get('title') or ''}\n{text_body}".strip()
                 matched = want(combined)
-                if not matched and not text_body.strip() and resolved_budget > 0 and e.get("subreddit") and e.get("id"):
+                # A complete relay record is the whole post (empty text = a title-only post);
+                # the post-page resolve (redlib / reddit.com) is for the old chain and cut records.
+                resolvable = not e.get("relay_complete")
+                if (not matched and not text_body.strip() and resolvable and resolved_budget > 0
+                        and e.get("subreddit") and e.get("id")):
                     resolved_budget -= 1
                     detail = await self.resolve_post(e["subreddit"], e["id"])
                     if detail:
@@ -1503,7 +1516,7 @@ class RedditClient:
                         matched = want(combined)
                 if not matched:
                     continue
-                if not text_body.strip() and resolved_budget > 0 and e.get("subreddit") and e.get("id"):
+                if not text_body.strip() and resolvable and resolved_budget > 0 and e.get("subreddit") and e.get("id"):
                     resolved_budget -= 1
                     detail = await self.resolve_post(e["subreddit"], e["id"])
                     if detail:
@@ -1568,7 +1581,8 @@ class RedditClient:
 
         if found is None:
             for e in unresolved[:2]:
-                detail = await self.resolve_post(e["subreddit"], e["id"])
+                # A complete relay record already carries the body (relay 0.0.8 / round 104).
+                detail = dict(e) if e.get("relay_complete") else await self.resolve_post(e["subreddit"], e["id"])
                 if not detail:
                     continue
                 merged_detail = {
```

## 3. Apply & verify

```bash
# in a Game-Express checkout on main @ 71202ee4 (or later; the touched regions are stable)
gh api -H "Accept: application/vnd.github.raw" \
  "repos/uesu/News-Express/contents/docs/handoffs/game-express-intake-reader.patch" > /tmp/gx-intake.patch
git am /tmp/gx-intake.patch                  # plain `git am` (a `--depth 1` clone cannot do --3way);
                                             # or: git apply /tmp/gx-intake.patch
pip install -r requirements.txt pyyaml ruff
python tests/test_reddit_intake.py           # REDDIT INTAKE TEST: ALL PASS (8 blocks)
python tests/test_smoke.py                   # 610/610 passed (count as of 71202ee4)
python tests/test_schedule_epithet_and_settled.py tests/test_gachawiki_placeholder.py   # and gachabase_kit / beta_sources
ruff check .                                 # All checks passed
DISCORD_BOT_TOKEN=x INTAKE_CHANNEL_ID=1 python -m gamexpress validate | grep "Reddit intake"
```

Also verified here inside a `sync_tree()` production checkout (`8mqzv4k2n7c` shape): both suites
pass there too. Open the PR, do **not** auto-merge; the owner merges.

## 4. Activation (owner, prod repo `uesu/8mqzv4k2n7c`)

The same two settings as News-Express (`7jkxmy9nvbc`) — one bot, one channel, both repos:

1. Secret `DISCORD_BOT_TOKEN` — a bot in the Citlali News server with *View Channel* + *Read
   Message History* on the intake channel and the **Message Content Intent** (for verified bots
   that intent must be *approved*; an unverified helper bot can simply toggle it).
2. Variable `INTAKE_CHANNEL_ID` — the intake channel id (the owner's `#modlogs`).

Nothing changes until both exist. Rollback: Variable `INTAKE_READER=off`. Step summary shows
`📡 reddit intake: relay ok — N record(s) in window, newest Ns; served r/…, u/…` when the relay
served a listing, or the fallback reason.

## 5. Record contract (written by Devvit `gaming-express` 0.0.8)

`v, id, sub, title, permalink, url, created (epoch s), author, flair, distinguished
(moderator|admin|null), spoiler, nsfw, score, comments, removed, xpost (parent fullname|null),
media[] (preview/i.redd.it images, v.redd.it fallback mp4 for videos), body (markdown, may be
cut), bodyTruncated`; 0.0.7 optional keys `full, mediaTruncated, edited, revision, xpostPermalink,
video{fallback,hls,gif}`; 0.0.8 optional key `resent (edited|approved, joined with +)`;
attachment `record.json` = the same record untrimmed + `parent`.
Update messages: `{"v":2,"kind":"update","at":<epoch>,"posts":[{id,sub,age,stage,removed,
deleted,edited,spoiler,nsfw,locked,score,comments}]}`. Subreddits polled: `AnantaLeaks, Genshin_Impact_Leaks,
HonkaiNexusAnimaLeaks, HonkaiStarRail_leaks, WutheringWavesLeaks, Zenlesszonezeroleaks_,
Genshin_Impact, HonkaiStarRail, ZZZ_Official, WutheringWaves, HonkaiNexusAnima, AnantaOfficial`;
accounts: `genshinimpact, HonkaiStarRail, HonkaiNexusAnima`. Poll every 5 minutes; a post
reaches the channel within one poll of its creation.
