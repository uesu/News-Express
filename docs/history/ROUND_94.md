# Round 94 (2026-10-28) — Twitter run diagnostics, run-result presence, opt-in 350 MiB cap

## Provenance

Sibling handoff from `uesu/Game-Express#85` (comment `6492593821`). It arrived as a
`git apply`-ready diff against `main` @ `8931a34`, which is exactly this branch's base, so
it applied cleanly. As with every previous handoff the claims were re-verified here rather
than trusted — this round's mutation table below is that verification.

## What changed

### Twitter run summary: a bounded *Diagnostics* block

The summary now counts five fixed categories from the captured log — Discord delivery
errors, FxTwitter fetch errors, unresolved media-heal lines, media-heal edit errors,
dedup-guard errors — and labels them **"matching log lines, not unique posts"**. Only
counts are printed; the log itself (which can contain webhook URLs and tokens in error
bodies) is never echoed.

The important half is the negative case: if the log is empty or missing, the block prints
`diagnostic coverage: unavailable (empty or missing log)` instead of five `0`s. This
matters more than it looks, because the workflow pipes the monitor through
`tee twitter_monitor.log` — the file exists from the first moment of the run — so "no
lines" is the normal shape of a crashed monitor.

### Twitter state line: `not-reached`

`TWITTER_CACHE_RESULT` is only set by the persist step (`failed` at entry, then
`no-changes`/`success`). When the monitor step fails, that step never runs and the
variable is unset; the summary used `:-failed`, which reported a cache failure that never
happened. It now reads `:-not-reached`, matching the wording the Reddit summary already
used.

### Reddit run summary: run-result presence

`**Run-result record:** read | missing | invalid shape | unreadable or malformed`. A
wrong-shaped or unparseable `reddit_run_result.json` was previously indistinguishable from
a clean empty run; now the summary says which one it is, and the record's contents are
never echoed.

### Opt-in 350 MiB video cap

`TWITTER_HIGH_VIDEO_LIMIT` → `_video_size_limit()` → `VIDEO_SIZE_LIMIT` in **both** X
engines (`twitter_v3.py`, `twitter_v2_button_outside.py`). Strict opt-in: only
`1`/`true`/`yes`/`on` select 350 MiB; unset, empty, `0`, `false`, `off`, `350`, `garbage`
keep 256 MiB. `twitter_monitor.yml` maps the optional repository Variable, so the live cap
does not move until a maintainer sets it.

## Verification beyond the handoff

The handoff's own tests cover the summary strings and both cap boundaries. These are the
things they did **not** pin, added here as `r94` contracts, each proven by mutation:

| Guard | Mutation that must fail it | Result |
|---|---|---|
| empty-but-existing log stays `unavailable` | force the counts branch on (`if true; then`) | fails, as intended |
| every diagnostic pattern still matches an engine log line | rename `Discord error [0-9]` in the workflow | fails, as intended |
| the Variable is mapped in the Twitter workflow only | delete the `TWITTER_HIGH_VIDEO_LIMIT:` mapping | fails, as intended |
| the run-result status is a closed vocabulary and never carries record content | append `raw[:60]` to the status string | fails, as intended |
| one source of truth for the cap | (structural: no second `256 * 1024 * 1024` literal, single `VIDEO_SIZE_LIMIT = _video_size_limit(...)` assignment) | — |

The vocabulary guard is the reason the last mutation is caught at all: the first version of
this check only asserted `"read" in summary` plus `secret not in summary`, and a truncated
`raw[:60]` echo slipped past it because the marker key sat past the cut. Asserting the
whole line against `^(read|missing|invalid shape|unreadable or malformed)$` closes that.

Facts re-checked directly rather than assumed:

* all five diagnostic patterns match real `logging.*` call sites in `twitter_v3.py`
  (`Discord error {status}`, `Error fetching FxTwitter data`, `media still unresolved
  after`, `MEDIA-HEAL {key}: edit HTTP`/`edit error`, `DEDUP GUARD:`);
* `GALLERY_VIDEO_LIMIT` is not set in any workflow, so `effective_limit =
  GALLERY_VIDEO_LIMIT or VIDEO_SIZE_LIMIT` really does follow the raised cap — there is no
  second 256 MiB ceiling behind it;
* `TWITTER_HIGH_VIDEO_LIMIT` appears in `twitter_monitor.yml` only. Reddit's
  `MAX_MEDIA_BYTES` (256 MiB) is a separate constant and is untouched;
* V3 is the engine the workflow actually runs (`run: python "testing area/twitter_v3.py"`);
  V2 is the documented alternative the same env reaches when a maintainer switches the run
  line.

## Verification

| Check | Result |
|---|---|
| `python -m compileall -q "testing area" tests .github/scripts` | clean |
| `python tests/test_smoke.py` | `SMOKE TEST: ALL PASS` — 1189 PASS, 0 FAIL (6 new `r94` contracts) |
| `python tests/test_twitter_media.py` | `ALL PASS` (256/257/350/351 MiB selection boundaries for both engines) |
| `python tests/test_reddit_signals.py` | `ALL PASS (103 pass)` |
| production-shaped checkout (`sync_prod.sync_tree`, no `README.md`/`docs/`) | smoke **1184 PASS**, twitter media **ALL PASS**, reddit signals **103 PASS** |
| `zizmor 1.31.1`, before vs after | byte-identical finding set (55, including the pre-existing high `dangerous-triggers`), **0** `ref-version-mismatch` |
| YAML parse of all workflows + `dependabot.yml` | ok |
| `pyflakes` on the touched engines | unchanged from base |

No new requests, no change to discovery, posting, `DISCOHOOK_PREVIEW`, the proxy chain,
crossposts, video/audio handling or gallery layout; no production writes and no
`sync_prod` run.

## Limits

- **The 350 MiB ceiling is not proven.** Discord's media proxy accepted 191 MB and rejected
  405 MB in the original measurement; 350 MiB sits inside that unverified band. Offline
  tests prove the *selection logic* at each boundary, not that Discord plays a 300–350 MiB
  proxy asset. That is exactly why the default stays 256 MiB and why the workflow only
  reads an unset Variable.
- Diagnostic counts are matching log lines. Five duplicate lines for one post count five,
  and a wording change in the engine would silently zero a category — which is the drift
  the `r94` parity guard exists to catch, but only for the patterns it knows.
- The run-result status describes the file, not the run: `read` means the record parsed,
  not that every field in it is meaningful.
- `docs/` and `README.md` never reach `uesu/7jkxmy9nvbc` / `uesu/wvkhabh2s22`; the two
  workflow changes and both engines reach production through `sync_prod.yml` after merge.
  This round did not trigger that sync.
