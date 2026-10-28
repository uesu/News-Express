# Round 93 (2026-10-28) — Removed link-spam liveness and Redlib removal comments

## Provenance

The sibling Game-Express audit (spec `news express new update enhancement.txt` in
`uesu/8mqzv4k2n7c`) reported one production leak. Unlike the earlier rounds this arrived
as prose plus code excerpts, not as an appliable diff, so every hunk was re-implemented
against this repository's current source and then verified the same way: **revert the
hunk, watch the matching guard fail**.

## The leak (production run `#10864`)

`Genshin_Impact_Leaks_1xh7jl3` — "Daily Free PSN Codes" by `u/Chef-Goat`, an external spam
link — was posted **after Reddit had already removed it** (AutoModerator karma threshold,
then Reddit's own spam filter).

| Stage | What production actually did |
|---|---|
| discovery | the post was **absent** from the live RSS feed (`100` entries, one clean fetch), so it entered through `_ArcticEntry` with `feed_ok=False` |
| `vxreddit` | HTTP `200`, but only its generic `vxReddit` shell title and no media → fetch miss (correct) |
| `redditez` | `"No data"` → miss (correct) |
| `embeddit` | HTTP `200` with the **pre-removal title**, the external URL as `body`, and `media=[]` |
| liveness | `verify_archive_post_live` returned `(True, "live via embeddit")` on that stub |

The root cause is not this monitor's plumbing: upstream **Embeddit ignores
`removed_by_category` on removed non-self link/media posts**. A media-less `embeddit`
answer is therefore evidence of "the post object still exists upstream", not of "the post
is live on Reddit". For an archive-only candidate that was the only vote cast.

## What changed

### `testing area/reddit_signals.py` (pure, stdlib only)

* `_REMOVED_NOTICE_RES` gains the two 2026 removal shapes: Redlib's
  `[removed] — [view removed post](…)` placeholder body and Reddit's
  `[ Removed by Reddit on account of … ]` policy banner.
* `redlib_moderator_removal_reason(page_html)` — reads Redlib's comment blocks and
  matches an **official** removal comment: the author must look official
  (`AutoModerator`, `*-ModTeam`, or a `comment_author … moderator` header) *and* the body
  must carry a past-tense removal sentence. Quoted text (`<blockquote>`) is stripped
  before matching; routine stickies, future-tense warnings ("will be removed") and
  ordinary user replies never match.
* `external_non_reddit_url(raw)` / `redlib_external_post_url(page_html)` — the
  `<a id="post_url">` target when it is a single bare non-Reddit URL.

### `testing area/reddit_proxy.py`

`_fetch_vxreddit` still returns `None` on the HTTP-200 `vxReddit` shell (r51 unchanged),
but now records the path in `_vxreddit_placeholder_paths`, with
`vxreddit_saw_placeholder()` / `clear_vxreddit_placeholders()`. That is the difference
between "Reddit answered and the page is a shell" and "vxReddit itself failed" — the
signal the spam-filter case needs. The set is cleared per run in `main()`.

### `testing area/reddit_main_v3.py`

* `verify_archive_post_live` keeps its exact 4-parameter signature. A media-less
  `embeddit` result is **held** (`embeddit_text_only`) instead of verifying an archive
  candidate, and the Redlib fallback then decides:
  * probes the verified post-page mirrors first (`_REDLIB_POST_FAST_HOSTS`), then the
    rest, stopping at the first parsed page;
  * rejects on a removal body (`removed_post_reason`), on an official removal comment,
    or — when vxReddit saw the placeholder — on an external `post_url` that contradicts
    the title;
  * with no post page at all, an external `embeddit` body plus the placeholder is also a
    rejection (the filter case where Redlib is unreachable).
* `live_removal_reason` (retraction) uses the same signals and stops at the first parsed
  page instead of walking all 28 mirrors.
* `base_from_redlib_page` keeps hyphens inside usernames: the live author is
  `u/Chef-Goat`, and the old `[A-Za-z0-9_]` class truncated it to `Chef`.

## What deliberately did NOT change

| Surface | State |
|---|---|
| live RSS candidate (`feed_ok=True`) | media-less `embeddit` still verifies it immediately, **0 extra requests** |
| archive candidate whose `embeddit` answer has media | verified immediately, **0 extra requests** |
| `REDDIT_RSS_INSTANCES` (28), `PROXY_SERVICES`, `DISCOHOOK_PREVIEW` | untouched |
| inline/CMAF video resolution, crosspost hydration | untouched |
| `verify_archive_post_live` signature | unchanged (4 parameters) |
| `reddit_signals.py` purity | still stdlib only (`html`, `urllib.parse` are stdlib) |
| the round-67 removed content-gate token | still absent from engine, signals, workflows |

## Verification

Per-hunk control runs — each mutation reverted the fix and the suite was re-run:

| Reverted hunk | Guards that failed |
|---|---|
| media-less `embeddit` rule | 5 `r93` contracts (replay, fast-mirror order, silent spam, routine sticky, …) |
| `redlib_moderator_removal_reason` in liveness | the `1xh7jl3` replay contract |
| external `post_url` corroboration | the silent-spam contract |
| hyphenated author class | the `u/Chef-Goat` contract |
| fast-mirror-first ordering | the probe-order contract |
| `live_removal_reason` changes | both retraction contracts |
| placeholder recording in `_fetch_vxreddit` | the placeholder-recorder contract |

Full runs (all four CI gates):

| Check | Result |
|---|---|
| `python -m compileall -q "testing area" tests` | clean |
| `python tests/test_reddit_signals.py` | `ALL PASS (103 pass)` — 8 new `r93` guards |
| `python tests/test_twitter_media.py` | `ALL PASS` |
| `python tests/test_smoke.py` | `SMOKE TEST: ALL PASS` — 1175 PASS, 0 FAIL (11 new `r93` contracts) |
| production-shaped checkout (`sync_prod.sync_tree`, no `README.md`/`docs/`) | smoke **1170 PASS**, reddit signals **103 PASS** |
| `pyflakes` on engine + `reddit_signals.py` | unchanged from base (no new issue) |
| `reddit_run_result.json` | absent (no scratch artifact committed) |

## Limits

- Nothing here was exercised against live Reddit from this sandbox (no network in CI).
  The `1xh7jl3` case is a replay of the recorded production shapes — the same status as
  the round-47/60/74 contracts — so the next live monitor tick after merge is the real
  confirmation.
- The external-`post_url` signal is deliberately conservative: it fires only together
  with the vxReddit placeholder. A legitimate external link post served normally (no
  placeholder, i.e. vxReddit down for everyone that run) is verified, and that is pinned
  by a contract.
- A post removed with **no** Redlib page, **no** removal marker and **no** placeholder
  evidence still cannot be distinguished from a healthy one by this monitor; that
  residual case is limited to posts whose content Reddit itself never serves.
- One extra Redlib page request happens only for an archive-only candidate whose
  `embeddit` answer was media-less — the exact population that leaked. RSS posts and
  media-bearing archive posts are unaffected.
- `docs/` and `README.md` never reach `uesu/7jkxmy9nvbc` / `uesu/wvkhabh2s22`; the engine
  and test changes reach production through `sync_prod.yml` after merge, which this
  round deliberately did **not** trigger.
