# Round 61 — prod deploy pack (copy–paste guide)

Sync BOTH live prod repos (`7jkxmy9nvbc` Reddit **and** `wvkhabh2s22` Twitter)
with the SAME six files. Round 61 is all-or-nothing per repo: the new smoke
guards require the merge script and both updated ymls, so never cherry-pick.
Updating `twitter_monitor.yml` inside the Reddit repo changes nothing about
the live Twitter bot — each prod repo runs only its own monitor.

## Part 1 — whole-file copy (4 files, replace entire contents)

Copy each file from News-Express exactly as-is:

| # | File | Action |
|---|---|---|
| 1 | `.github/workflows/reddit_monitor.yml` | replace whole file (260 lines) |
| 2 | `.github/workflows/twitter_monitor.yml` | replace whole file (194 lines) |
| 3 | `.github/scripts/merge_monitor_caches.py` | **NEW file** (172 lines) |
| 4 | `docs/ROUND_61.md` | **NEW file** (165 lines) |

## Part 2 — `tests/test_smoke.py` (2 edits — do NOT replace the whole file)

### Edit 2a — update the round-39 cache-persistence guard

FIND the existing block starting with
`for _r39_wf in (".github/workflows/reddit_monitor.yml", ".github/workflows/twitter_monitor.yml"):`
that contains the `r39 cache persistence` checks (it currently pins the old
`git pull --rebase` recovery) and REPLACE that whole `for` block with:

```python
for _r39_wf in (".github/workflows/reddit_monitor.yml", ".github/workflows/twitter_monitor.yml"):
    with open(os.path.join(ROOT, _r39_wf), encoding="utf-8") as _fh:
        _r39_source = _fh.read()
    check(f"r39 cache persistence: {_r39_wf} uses staged-only no-change detection",
          "git diff --cached --quiet" in _r39_source)
    # r61 (2026-10-04) UPDATE: the recovery between retries changed from
    # `git pull --rebase` (conflict-fragile — the 2026-10-03 double post's
    # accomplice) to the semantic JSON merge (fetch + reset + merge script).
    # The detached-HEAD-safe push and the 3-attempt loop are unchanged.
    check(f"r39 cache persistence: {_r39_wf} retries an explicit detached-HEAD-safe push",
          'for attempt in 1 2 3; do' in _r39_source
          and 'git push origin "HEAD:${cache_branch}"' in _r39_source
          and 'git fetch origin "$cache_branch"' in _r39_source
          and "merge_monitor_caches.py" in _r39_source)
    check(f"r39 cache persistence: {_r39_wf} fails loudly if a dedup cache cannot persist",
          "::error::CACHE PUSH FAILED" in _r39_source
          and "::error::CACHE PUSH RECOVERY FAILED" in _r39_source)
```

### Edit 2b — append the round-61 guard block

FIND the final

```python
if failures:
```

at the very bottom of the file and PASTE this block immediately ABOVE it
(keep one blank line before `if failures:`):

```python
# ---------------------------------------------------------------------------
# ROUND 61 (2026-10-04): stale-tip double post + conflict-fragile cache push.
# Live incident 2026-10-03: prod run #4014 was dispatched while another run
# was executing; workflow_dispatch pins GITHUB_SHA at DISPATCH time, so the
# queued run started on the stale tip dd756a5 — six seconds after cache
# commit 2de1491 (already containing Genshin_Impact_Leaks_1wwyure) — and
# posted 1wwyure a second time. Its own cache push then died on a git LINE
# conflict in pending_reddit.json that a semantic JSON merge resolves
# trivially. Two fixes, both guarded here:
#   (1) a "Sync to the live branch tip" step in BOTH monitor workflows;
#   (2) the persist step recovers via .github/scripts/merge_monitor_caches.py
#       (semantic union merge) instead of `git pull --rebase`.
# ---------------------------------------------------------------------------
import importlib.util as _r61_ilu
import subprocess as _r61_sp
import tempfile as _r61_tmp

_r61_script = os.path.join(ROOT, ".github", "scripts", "merge_monitor_caches.py")
check("r61: merge_monitor_caches.py exists", os.path.isfile(_r61_script))

_r61_spec = _r61_ilu.spec_from_file_location("_r61_merge", _r61_script)
_r61_mod = _r61_ilu.module_from_spec(_r61_spec)
_r61_spec.loader.exec_module(_r61_mod)

# (a) EXACT INCIDENT REPLAY — both sides appended the same key, evictions
# diverged, pending last_checked collided on the same entry.
_r61_theirs_posted = ["A_1", "B_2", "Genshin_Impact_Leaks_1wwyure"]
_r61_ours_posted = ["A_1", "B_2", "Genshin_Impact_Leaks_1wwyure", "C_3"]
_r61_posted = _r61_mod.merge_lists(_r61_theirs_posted, _r61_ours_posted)
check("r61: posted merge is a strict union (no dedup key ever lost)",
      set(_r61_posted) == set(_r61_theirs_posted) | set(_r61_ours_posted))
check("r61: posted merge never duplicates a key (double-add collapses to one)",
      _r61_posted.count("Genshin_Impact_Leaks_1wwyure") == 1
      and len(_r61_posted) == len(set(_r61_posted)))
_r61_pending = _r61_mod.merge_dicts(
    {"HNA_1wwnu46": {"first_seen": 1.0, "last_checked": 100.0, "reason": "media_wait"},
     "only_theirs": {"first_seen": 2.0, "last_checked": 2.0, "reason": "removal_notice"}},
    {"HNA_1wwnu46": {"first_seen": 1.0, "last_checked": 200.0, "reason": "media_wait"},
     "only_ours": {"first_seen": 3.0, "last_checked": 3.0, "reason": "removal_notice"}})
check("r61: pending merge keeps both one-sided entries and newest last_checked",
      _r61_pending["HNA_1wwnu46"]["last_checked"] == 200.0
      and "only_theirs" in _r61_pending and "only_ours" in _r61_pending)

# (b) End-to-end through the CLI exactly as the workflow invokes it, plus
# the hygiene rule (pending keys covered by the merged posted list drop out)
# and the loud failure on invalid JSON (a half-merge must never be pushed).
with _r61_tmp.TemporaryDirectory() as _r61_d:
    _r61_ours = os.path.join(_r61_d, "ours"); os.mkdir(_r61_ours)
    _r61_repo = os.path.join(_r61_d, "repo"); os.mkdir(_r61_repo)
    with open(os.path.join(_r61_repo, "posted_reddit.json"), "w") as _f:
        json.dump(_r61_theirs_posted, _f)
    with open(os.path.join(_r61_ours, "posted_reddit.json"), "w") as _f:
        json.dump(_r61_ours_posted, _f)
    with open(os.path.join(_r61_repo, "pending_reddit.json"), "w") as _f:
        json.dump({"Genshin_Impact_Leaks_1wwyure": {"first_seen": 1.0,
                   "last_checked": 1.0, "reason": "media_wait"}}, _f)
    with open(os.path.join(_r61_ours, "pending_reddit.json"), "w") as _f:
        json.dump({"D_4": {"first_seen": 4.0, "last_checked": 4.0,
                   "reason": "media_wait"}}, _f)
    _r61_run = _r61_sp.run(
        [sys.executable, _r61_script, _r61_ours, _r61_repo,
         "posted_reddit.json", "proxy_health.json", "pending_reddit.json",
         "posted_messages.json"],
        capture_output=True, text=True)
    with open(os.path.join(_r61_repo, "pending_reddit.json")) as _f:
        _r61_cli_pending = json.load(_f)
    check("r61: CLI merge succeeds with the workflow's exact argument shape",
          _r61_run.returncode == 0, _r61_run.stderr[:200])
    check("r61: hygiene — a pending key already in the merged posted list drops",
          "Genshin_Impact_Leaks_1wwyure" not in _r61_cli_pending
          and "D_4" in _r61_cli_pending)
    with open(os.path.join(_r61_repo, "pending_reddit.json"), "w") as _f:
        _f.write("{broken")
    _r61_bad = _r61_sp.run(
        [sys.executable, _r61_script, _r61_ours, _r61_repo,
         "pending_reddit.json"], capture_output=True, text=True)
    check("r61: invalid JSON fails LOUDLY (non-zero, no half-merge pushed)",
          _r61_bad.returncode != 0 and "SEMANTIC MERGE FAILED" in _r61_bad.stderr,
          _r61_bad.stderr[:200])

# (c) Both monitor workflows carry the sync-to-tip step and the semantic
# recovery, and the old conflict-fragile rebase recovery is gone.
for _r61_wf in (".github/workflows/reddit_monitor.yml",
                ".github/workflows/twitter_monitor.yml"):
    with open(os.path.join(ROOT, _r61_wf), encoding="utf-8") as _f:
        _r61_src = _f.read()
    _r61_base = os.path.basename(_r61_wf)
    check(f"r61: {_r61_base} — sync-to-tip step present (stale GITHUB_SHA fix)",
          "Sync to the live branch tip" in _r61_src
          and "git reset --hard FETCH_HEAD" in _r61_src)
    check(f"r61: {_r61_base} — persist recovery is the semantic merge",
          "merge_monitor_caches.py" in _r61_src)
    check(f"r61: {_r61_base} — conflict-fragile rebase recovery removed",
          "git pull --rebase" not in _r61_src)
    check(f"r61: {_r61_base} — dispatch-time SHA pinning documented",
          "GITHUB_SHA" in _r61_src and "dispatch" in _r61_src.lower())

```

## Part 3 — `README.md` (2 edits — do NOT replace the whole file)

### Edit 3a — Cadence combos section

FIND the line `## 🗒 Changelog` and PASTE this immediately ABOVE the `---`
divider that precedes it (i.e. right after the Speed presets rollback
paragraph):

```markdown
### Cadence combos (5 / 3 / 2 minutes)

Any cadence **below 5 minutes requires the round-61 workflows** (the
sync-to-tip step + the semantic cache merge — shipped in both monitor
ymls). The 2026-10-03 double post happened at a 2–3-minute cadence on the
pre-round-61 workflows: a queued `workflow_dispatch` run starts on the tip
pinned at *dispatch* time, i.e. without the previous run's fresh dedup
cache. With round 61 in place, correctness is cadence-independent.

| Cron | Variables | Typical arrival | Notes |
|---|---|---|---|
| **5 min** (default) | none — or any preset above | ~5–10 min (Instant: 0–5) | queue overlaps ~never happen; the safest grid |
| **3 min** | `POST_SETTLE_SECONDS=120`, `APPROVAL_RECHECK_SECONDS=180` | ~3–6 min | balanced middle; recheck matches every other tick |
| **2 min** | `POST_SETTLE_SECONDS=120`, `APPROVAL_RECHECK_SECONDS=120` | ~2–4 min | the Faster preset; expect occasional superseded-queued-run cancellations in the Actions list (benign — a skipped tick, the next tick reads the same feed) |

---

```

### Edit 3b — round-61 changelog entry

FIND the line `## 🗒 Changelog` and PASTE this as the FIRST bullet right
below it (above the 2026-10-03 Instant-preset entry):

```markdown
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
```

## Part 4 — after merging (both repos)

1. CI must be green: smoke + signals suites all pass (the 15 new `r61:` guards included).
2. No Variables/Secrets changes, no cron changes needed — correctness is now cadence-independent.
3. First run after merge behaves identically; the sync-to-tip step just prints `Now at <sha> (live main tip).`
4. Posting speed is unchanged on both bots: the only added runtime is one
   `git fetch` + `git reset --hard` (~1–2 s) BEFORE the feed is read.
