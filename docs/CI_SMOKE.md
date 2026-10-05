# 🧪 CI + smoke test — full explanation (optional or required?)

> **TL;DR:** `.github/workflows/ci.yml` + `tests/test_smoke.py` are
> **REQUIRED for this repo's setup** — not optional. They are the ~15–30-second
> offline safety gate that runs on **every commit/PR** (including
> Dependabot's) and is the *only* thing that proves a script still imports
> and behaves **before** it can post to Discord. Deleting them doesn't break
> the monitor immediately, but it removes the protection that makes
> Dependabot **auto-merge** (and any one-line bump) safe to enable.

---

## 1. What are the two pieces?

| Piece | What it is | What it runs |
|---|---|---|
| `.github/workflows/ci.yml` | A GitHub Actions workflow that triggers on **every push and PR** (public repo = free) | Sets up exact **CPython 3.14.7**, then runs `pip install -r requirements.txt` → `python -m compileall` over every script → `python tests/test_smoke.py` |
| `tests/test_smoke.py` | An **offline** test (no network, no secrets, no Discord): every monitor script must **import cleanly**, the Reddit V3 card pipeline and safety gates must still behave (body cleaning, media extraction/dedup, i.redd.it swap, redlib scoping, OP comment, Components V2 layout, proxy parsers, archive/liveness gates, and — round 51 — `/user`, `/u`, and `/r/u_` profile-crosspost headers plus the media-less vxReddit shell fallback). The X V3 path is also pinned for GIF conversion, fallback parsing/order, and — round 51 — a visible but still deduplicated cached `TEST_TWEET_ID` skip. | `python tests/test_smoke.py` — prints `PASS`/`FAIL` per check, exits non-zero on any failure |

## 2. Optional or required? — **Required (for how this repo is set up)**

| Question | Answer |
|---|---|
| Does the *monitor itself* import ci.yml? | No — `reddit_monitor.yml` never calls it. The monitor runs fine with ci.yml deleted. |
| So why is it required here? | Because this repo ships **Dependabot** (+ opt-in **auto-merge**) and a multi-file **testing-area workflow**. The CI job is the gate those rely on: Dependabot's auto-merge (and the 60-second manual review in `docs/DEPENDABOT.md` §7) is defined as "green checks + one-line diff = safe". **No CI = no green check = auto-merge must be turned off** and every PR (including your own pastes) loses its fast safety net. |
| What catches what? | A dependency bump that renames an API → `pip install` or the import check fails **before merge**. A paste that mangles a file (the round-12 backslash incident!) → `compileall` or the import check fails in ~15–30 s — **before any cron run can post** a broken card. |
| Does it post to Discord? | Never. It has no webhook, no secrets, no network access (the test deliberately runs offline with stubbed `aiohttp`/`feedparser`/`dotenv`). |
| Does it consume minutes? | Public repo: the check runs are free. Runtime ~15–30 s. |
| Can I delete it? | Technically yes — the monitor keeps running. You would then (a) disable `AUTO_MERGE_DEPENDABOT` (auto-merge requires "at least one check"), (b) lose the pre-merge catch for any file edit, and (c) find syntax errors only when a live run fails. Not recommended. |

## 2a. Python runtime coverage

The CI workflow deliberately pins **CPython 3.14.7** in the same way as both
live monitor workflows. That makes a green PR the proof that the exact runtime
can install the current dependencies, compile every script, and pass the
offline behavioral suite. It does not contact Discord or external feeds; after
a runtime bump, follow CI with the documented safe monitor dry-run.

Dependabot does not manage this `python-version` workflow input. The version is
updated by an explicit reviewed PR so a CPython patch cannot silently reach a
live posting run. Full compatibility, performance, automation, and rollback
policy: [Python runtime policy](PYTHON_RUNTIME.md).

## 3. Why the smoke test is written the way it is

* **Offline by design** — it must run on GitHub runners and on any machine
  without the real environment: `aiohttp`, `feedparser` and `dotenv` are
  stubbed if not installed, and no check opens a connection.
* **Import gate for every engine** — all monitor scripts
  (`testing area/twitter_v1.py`, the X V2/V3 test copies + the
  `testing area/twitter_proxy.py` fallback module, Reddit V1/V2/V3,
  `testing area/video_diag.py`) must import without error.
  This is the check that fails on a mangled paste or a breaking dependency
  bump.
* **Pipeline checks** — the Reddit V3 card logic is exercised with fixtures
  (body cleaning, media dedup/best-rendition, i.redd.it swap, redlib
  post-area scoping, test-post native base, OP comment selection,
  components-v2 layout + button set, 4000-char budget, and — round 13 — the
  proxy-service parsers: Embeddit status-id codec, og-tag parsing, stats
  lines, the redditez/embeddit JSON shapes, fallback-chain skipping, the
  `proxy_health.json` round-trip, — round 56 — the videos-only media-heal scope
  (`is_video_media_url`/`heal_eligible_items` + the `MEDIA_HEAL_SCOPE`
  value matrix `video`/`on`/`all`/`off`), and — rounds 53/54 — the GHA-safe string
  Variable defaults, the Embeddit-rewrite Component-Embed page parser, and
  the Mastodon→component→unavailable mode machine).
* **Listing fixtures (originally round 38e)** — the `/new` listing reads
  behind the round-64 pristine listing confirmation and the round-44
  retraction seatbelt are exercised offline. The real `_fetch_new_listing()`
  runs against an in-memory listing document served by a fake session, which
  pins the round-64 pristine request shape: a unique `_fresh=` cache-buster
  per call plus `Cache-Control`/`Pragma` no-cache headers on every attempt.
  What the engine does with that snapshot is covered by the decision checks
  in both suites — `listing_absence_proves_dead` and `retraction_decision`
  (span arithmetic, the two-proof rule, `edit`/`delete`/off) — and by the
  round-64 end-to-end `main()` cases in `tests/test_reddit_signals.py`
  (listed → delivers; absent → skipped with no pending/tracker entry, then
  delivered on the first tick that lists it; a listing outage is never read
  as absence). Nothing here contacts Reddit.
* **Fail-loud** — any `FAIL` exits non-zero → red check → Dependabot PR
  (or your PR) cannot merge (or auto-merge).

## 4. Running it yourself (local)

```bash
pip install -r requirements.txt
python tests/test_smoke.py
```

Expected: a `PASS …` line per check ending with `SMOKE TEST: ALL PASS`.
It needs **no** `.env`, **no** secrets, and works fully offline.

## 5. When the check is red — what to do

1. Open the CI run → the failing step names the problem (install /
   compile / specific `FAIL …` line).
2. For a **Dependabot** PR: don't merge — Dependabot will try the next
   version on its own schedule (or you can close the PR).
3. For **your own** commit: fix the file, re-commit — the next push re-runs
   the gate automatically.
4. If a merged bump later misbehaves in a live run: *Revert* the merge
   commit (one click) — `docs/DEPENDABOT.md` §4.

---

*Files involved: `.github/workflows/ci.yml`, `tests/test_smoke.py`,
`.github/workflows/dependabot_auto_merge.yml` (the gate it waits on),
`docs/DEPENDABOT.md` (why the gate exists).*
