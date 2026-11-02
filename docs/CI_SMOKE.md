# 🧪 CI + smoke test — full explanation (optional or required?)

## Reddit table and continuation regressions

The same `tests/test_smoke.py` guards HTML-table preservation before RSS cleanup,
parity with Markdown row blocks, bold row headings, literal dates/unknown wording,
entity decoding, links and pipes, nested layout wrappers, sibling tables and
conservative fallback for spans/malformed shapes. The `1x9geq7` example is a
transcription from supplied screenshots, not a raw archive/API capture.

Continuations start with the remaining source text, without a generated
`(continued)` label or extra leading newline; source-authored wording is preserved.
Content-driven pagination replaces the old message cap; the 3800-character component
budget, accent and existing Markdown split rules remain. These checks are offline, not a live-post certification.
No cache reset, workflow edit or new configuration switch is required.

### Multi-page indicator and formatting preservation (2026-10-26)

Multi-page posts carry one generated subtext footer and nothing else: the main card
ends `… • 📜 Page 1/N`, each continuation ends `-# 📜 Page n/N`, and single-page
cards stay byte-identical (no `Page 1/1`). The page count is settled by a bounded
fixed-point loop, so the printed `N` always equals `1 + len(continuations)`.
Guards cover the 7-page `1xfcqx0` shape, the 4000-character ceiling, and the
round-66 gallery split that now expects the extra footer component.

Formatting preservation is checked through the real cleaners: `<strong>`/`<b>`,
inline-styled `<span>` bold, `<h1>`–`<h6>`, `<i>`/`<em>` and `<del>`/`<s>`/`<strike>`,
`####`–`######` Markdown subheadings and native `>!spoiler!<` outside code spans,
plus a tag-agnostic HTML-vs-Markdown router for JSON `selftext`. Text-only posts also
keep proxy-observed `💬`/`👍` counts (zero extra requests) and drop a sibling
wave's stats only when genuinely absent — counts are never fabricated. Fenced code
blocks and inline emphasis are closed and reopened across page boundaries within
budget. These are offline unit checks; they do not certify Discord playback.

## Crosspost and summary regressions

The existing `tests/test_smoke.py` includes crosspost/media cases and executes the
actual final-summary Bash from the two monitor YAMLs with local fixture logs.
It covers timestamped account/failure counting, missing measurements, measured
zero candidates, deliveries/cache results and reuse of archive misses/errors or
validated parent records. Run this script plus the existing Reddit signal and
Twitter media runners. No new test file, live webhook or cache reset is needed.

> **TL;DR:** `.github/workflows/ci.yml`, `tests/test_smoke.py`,
> `tests/test_reddit_signals.py`, and `tests/test_twitter_media.py` are
> **REQUIRED for this repo's setup** — not
> optional. They are the offline safety gate that runs on **every pull request**
> and on pushes to `main`, including Dependabot PRs. They prove that the
> scripts still install, compile, import, and satisfy the offline behavior
> guards before a change can be merged. Deleting them does not stop an already
> scheduled monitor immediately, but it removes the protection that makes
> Dependabot auto-merge and runtime bump review safe to use.

---

## 1. What are the pieces?

| Piece | What it is | What it runs |
|---|---|---|
| `.github/workflows/ci.yml` | A GitHub Actions workflow that triggers on **every pull request** and every push to `main` (public repo = free) | Sets up exact **CPython 3.14.9**, then runs `pip install -r requirements.txt` → `python -m compileall` over every script → `python tests/test_smoke.py` → `python tests/test_reddit_signals.py` → `python tests/test_twitter_media.py` |
| `tests/test_smoke.py` | An **offline** test (no network, no secrets, no Discord): every monitor script must **import cleanly**, the Reddit V3 card pipeline and safety gates must still behave (body cleaning, media extraction/dedup, i.redd.it swap, redlib scoping, OP comment, Components V2 layout, proxy parsers, archive/liveness gates, and — round 51 — `/user`, `/u`, and `/r/u_` profile-crosspost headers plus the media-less vxReddit shell fallback). The X V3 path is also pinned for GIF conversion, fallback parsing/order, and — round 51 — a visible but still deduplicated cached `TEST_TWEET_ID` skip. | `python tests/test_smoke.py` — prints `PASS`/`FAIL` per check, exits non-zero on any failure |
| `tests/test_reddit_signals.py` | A pure offline Reddit gate/decision suite for removal-notice classification, tombstones/retraction decisions, listing confirmation, main-loop signal behavior, and the round-67 policy guards (no content-advisory subsystem; video-quality selection + rollback). | `python tests/test_reddit_signals.py` — prints `PASS`/`FAIL` per check, exits non-zero on any failure |
| `tests/test_twitter_media.py` | A pure offline **X (Twitter) V3 media** suite (round 73): canonical source order (photo-only, video-only, mixed, legacy provider payloads), the GIF converter chain and its content-type rules, mp4-vs-AVIF priority, the direct-mp4 fallback, and the healthy-media / explicit-unresolved-evidence heal contract — with per-URL probe counts proving the healthy path costs no extra round-trip and that the AVIF last resort never re-probes the converter chain. | `python tests/test_twitter_media.py` — prints `PASS`/`FAIL` per check, exits non-zero on any failure |

## 2. Optional or required? — **Required (for how this repo is set up)**

| Question | Answer |
|---|---|
| Does the *monitor itself* import ci.yml? | No — `reddit_monitor.yml` never calls it. The monitor runs fine with ci.yml deleted. |
| So why is it required here? | Because this repo ships **Dependabot** (+ opt-in **auto-merge**) and a multi-file **testing-area workflow**. The CI job is the gate those rely on: Dependabot's auto-merge (and the 60-second manual review in `docs/DEPENDABOT.md` §7) requires green checks on the exact PR head before merge. **No CI = no green check = auto-merge must be turned off** and every PR (including your own pastes) loses its fast safety net. |
| What catches what? | A dependency bump that renames an API → `pip install` or the import check fails **before merge**. A paste that mangles a file (the round-12 backslash incident!) → `compileall` or the import check fails in ~15–30 s — **before any cron run can post** a broken card. |
| Does it post to Discord? | Never. It has no webhook, no secrets, no network access (the test deliberately runs offline with stubbed `aiohttp`/`feedparser`/`dotenv`). |
| Does it consume minutes? | Public repo: the check runs are free. Runtime ~15–30 s. |
| Can I delete it? | Technically yes — the monitor keeps running. You would then (a) disable `AUTO_MERGE_DEPENDABOT` (auto-merge requires "at least one check"), (b) lose the pre-merge catch for any file edit, and (c) find syntax errors only when a live run fails. Not recommended. |

## 2a. Python runtime coverage

The CI workflow deliberately pins **CPython 3.14.9** in the same way as both
live monitor workflows. That makes a green PR the proof that the exact runtime
can install the current dependencies, compile every script, and pass the
offline behavioral suite. It does not contact Discord or external feeds; after
a runtime bump, follow CI with the documented safe monitor dry-run.

Dependabot does not manage this `python-version` workflow input. The version is
updated by the dedicated runtime bump workflow so a CPython patch cannot
silently reach a live posting run. That workflow adds a wheels-only dependency
install (`pip install --only-binary=:all:`), pre-rewrite and post-rewrite
compile/test gates, an explicit current-runtime rewrite allowlist split into
required surfaces (present in every checkout) and optional dev-only ones
(`README.md`, `docs/*`, `sync_prod.yml` — skipped with a notice in the
production repositories), and manual review for new minor series such as Python
3.15. Full compatibility, performance, automation, and rollback policy:
[Python runtime policy](PYTHON_RUNTIME.md).

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
  post-area scoping, test-post native base,
  components-v2 layout + button set, 4000-char budget, and — round 13 — the
  proxy-service parsers: Embeddit status-id codec, og-tag parsing, stats
  lines, the redditez/embeddit JSON shapes, fallback-chain skipping, the
  `proxy_health.json` round-trip, — round 56 — the videos-only media-heal scope
  (`is_video_media_url`/`heal_eligible_items` + the `MEDIA_HEAL_SCOPE`
  value matrix `video`/`on`/`all`/`off`), and — rounds 53/54 — the GHA-safe string
  Variable defaults, the Embeddit-rewrite Component-Embed page parser, and
  the Mastodon→component→unavailable mode machine).
* **Listing fixtures (originally round 38e)** — the `/new` listing reads
  behind the optional round-44 retraction seatbelt are exercised offline
  (the former round-64 pristine listing confirmation used the same path with
  a unique `_fresh=` cache-buster per call plus `Cache-Control`/`Pragma`
  no-cache headers until its removal on 2026-10-21). The real
  `_fetch_new_listing()` runs against an in-memory listing document served by
  a fake session, which pins the current retraction listing request shape.
  What the engine does with that snapshot is covered by the decision checks
  in both suites — `listing_absence_proves_dead` and `retraction_decision`
  (span arithmetic, the two-proof rule, `edit`/`delete`/off) — and by the
  round-64 end-to-end `main()` cases in `tests/test_reddit_signals.py`
  (listed → delivers; absent → skipped with no pending/tracker entry, then
  delivered on the first tick that lists it; a listing outage is never read
  as absence). Nothing here contacts Reddit.
* **Workflow-surface guards (round 89)** — every `uses:` must be a 40-hex SHA
  pin carrying a bare `# vX.Y.Z` comment (prose goes on the line above: `zizmor`'s
  `ref-version-mismatch` audit only parses a comment it can read), every job must
  stay on `runs-on: ubuntu-latest` so runner OS updates roll forward, the runtime
  bump's rewrite shell is executed against temporary checkouts (with, without, and
  missing the dev-only `sync_prod.yml`), and the suite fails if its own stdout
  emits a GitHub Actions workflow command such as `::error::` — simulated faults
  belong in a captured buffer.
* **Fail-loud** — any `FAIL` exits non-zero → red check → Dependabot PR
  (or your PR) cannot merge (or auto-merge).

## 4. Running it yourself (local)

```bash
pip install -r requirements.txt
python -m compileall -q "testing area" tests
python tests/test_smoke.py
python tests/test_reddit_signals.py
python tests/test_twitter_media.py
```

Expected: `PASS …` lines ending with `SMOKE TEST: ALL PASS`, a final
`ALL PASS` from the Reddit signal suite, and `TWITTER MEDIA TEST: ALL PASS`
from the X media suite. They need **no** `.env`, **no**
secrets, and work fully offline.

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
`tests/test_reddit_signals.py`, `tests/test_twitter_media.py`,
`.github/workflows/dependabot_auto_merge.yml`
(the gate it waits on), `docs/DEPENDABOT.md` (why the gate exists), and
`docs/PYTHON_RUNTIME.md` (runtime-bump-specific validation).*

## Twitter recovery revalidation

The focused Twitter media suite verifies GET revalidation before queued PATCH recovery:
resolved during delay means zero edits; explicitly unresolved media keeps identical-payload
recovery; 401/403/404 stops recovery; unavailable GET retains the bounded prior behavior.
Each queued attempt adds at most one GET. An ordinary healthy post incurs no new request.

## Full-body continuation delivery (2026-10-25)

The smoke suite supersedes the old cap assertions with exact complete-content checks:
part five, over 40k characters, more than ten pages and long tokens. Mocked Discord
responses exercise the actual delivery helper, disk persistence with retraction disabled,
429 deferral/resume without repeating accepted pages, all message IDs and holds after
missing IDs, 500 responses and timeouts. Failed serialization leaves the prior cache intact;
invalid JSON/object shapes fail closed. Full-post delivery preserves source ordering and
main-card geometry. Live Discord playback and production delivery are not asserted.

The completed-continuation restart regression runs the real main loop with a persisted
completed record and a missing ordinary dedup file. A repeated feed entry performs no
post-data/media lookup or Discord send, restores dedup and retains all recorded IDs.

Round 88 integration also covers a main-card timeout with the hold saved before POST,
explicit main rejections versus uncertain server errors, restart suppression of an
ambiguous main, and retention after completing a continuation older than six hours.
Nested malformed continuation progress is rejected before any resumed send.

Pre-send connector failures separately verify retryable continuation deferral and release
of an unsent main-card hold; timeouts and HTTP server errors still require reconciliation.
