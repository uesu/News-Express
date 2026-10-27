# Round 92 (2026-10-27) — Redlib fleet, inline rich-text video, crosspost media, request savings

## Provenance

This round implements the companion patch in
`uesu/Game-Express#82#issuecomment-6444761324` (its own numbering calls this "Round 90";
this repository already used round 90 for the multi-page `📜 Page X/Y` work, so every guard
here is `r92:` and the section headers say round 92). The patch touched exactly two files
here — `testing area/reddit_main_v3.py` and `tests/test_smoke.py` — and applied cleanly on
the current `main` with `git apply --check`.

Everything below was executed and re-verified in this repository. The sibling's claims are
treated as leads, not proof: anything that could not be checked from this sandbox is called
out under **Limits** and is worded as such in the code comments too.

## What changed

### 1. Redlib fleet: 25 → 28 members (0 deletions)

`REDDIT_RSS_INSTANCES` gains three tail entries — `https://r.naa.gg`,
`https://redlib.thepixora.com`, `https://redlib.r4fo.com` — with the prior 25 kept in their
exact order. `https://redlib.cow.rip` is deliberately **not** added (Cloudflare interstitial
plus a looping custom verification wall); the fleet guard asserts its absence so it cannot
sneak back in. `reddit_main.py` and `reddit_main_v2_embedez.py` are untouched, and
`PROXY_SERVICES` is still exactly `("vxreddit", "redditez", "embeddit")`.

Also **unverified from here**: the three new hosts are sibling-reported. CI has no network
access, so this round proves the *shape* of the fleet, not that each host answers today.

### 2. Inline rich-text video and mixed media

New: `INLINE_REDDIT_VIDEO_RE`, `REDDIT_VIDEO_LINE_URL_RE`, `extract_all_reddit_video_ids`,
`extract_all_redlib_video_ids`, `metadata_video_ids`, `_post_has_nonvideo_media`,
`_meta_entry_to_media_item`, `arctic_media_items`, `_has_inline_photo_urls`.

- `extract_vreddit_id` also parses `/link/<post>/video/<id>/player`, but returns `None` when
  the same text carries inline photos — a mixed post is then finished by the supplement pass
  instead of being half-resolved at base time.
- `arctic_video_info` detects a **pure single inline video** (`media=None`,
  `media_metadata[id]["e"] == "RedditVideo"`, selftext player link) and returns
  `(id, None)`; `VREDDIT_RE` is now case-preserving (`[A-Za-z0-9]+`).
- `resolve_post_media` gains a supplement pass that collects unseen video IDs from the final
  body, `content_html`, the Arctic record, the hydrated crosspost original, the structured
  crosspost parent, and the full JSON — resolving each **once per post** (`_attempted_vids`,
  seeded from media that already resolved, so a failed primary video is never retried). A
  resolved extra video is marked `gallery=True` when other media is present, which is what
  makes the photo gallery and the video gallery render as separate V2 containers.
- `_drop_gallery_media_lines` keeps prose, captions, and *unresolved* links while dropping
  resolved video URL lines, bare or self-labelled, across `/player`, `v.redd.it`, and the
  embed-mirror forms.

### 3. Crossposts from unmonitored subreddits

When the parent is known only by ID (`t3_<id>`, no path), one Arctic lookup hydrates it,
recovers the permalink (or synthesises `/r/<sub>/comments/<id>/` from the record's
subreddit), and resolution proceeds with real media and real attribution. `arctic_media_items`
covers ordered galleries, rich-text `media_metadata` image/GIF sets, and a single
`i.redd.it`/`preview.redd.it` destination; `_arctic_media_hint` unwraps the original so a
media-less child post still counts as media-bearing.

### 4. Request savings

`enrich_gallery_redlib` splits the fleet into Wave 1 (the 10 verified post-page-capable
mirrors, probed first) and Wave 2 (the other 18), and only falls back when Wave 1 answers
nothing. This is the "10 requests instead of 28" saving, and it also resolves inline video
when a post page has no photos. `resolve_video_url` is additionally memoised per post via
`_attempted_vids`.

## What this branch kept from the sibling patch, and what it changed

Kept verbatim: the engine hunks, the `1xgnbtu → 1xgncao` end-to-end fixture, the mixed
photo+video fixture, the three external-crosspost cases, the dead-video single-probe case,
and the Wave-1 savings assertion.

Changed on purpose:

1. **Guard numbering `r90` → `r92`** everywhere in the imported block, plus the fleet guard
   text and docstring. Guards are historical identifiers here; two different `r90:` families
   would make failures ambiguous.
2. **The `DISCOHOOK_PREVIEW` guard was vacuous** — `os.environ.get(..., "1") == "1" or
   hasattr(...)` is true regardless of the source. It now pins the real form
   (`DISCOHOOK_PREVIEW = _env_flag("DISCOHOOK_PREVIEW", "1")`), proves `_env_flag`'s default
   semantics with an unset name, and asserts `reddit_proxy.py` does not grow its own copy.
3. **Two new guards for the savings claim.** The patch asserted the Wave-1 win but not the
   "0 coverage loss" half: `r92` now proves the two waves are a partition of the fleet (no
   host added, dropped, or probed twice) and that a **Wave-2-only** mirror still resolves,
   with Wave 1 exhausted first in fleet order.
4. **One regression guard for the photo heuristic**: `extract_vreddit_id` still returns the
   ID for a plain `v.redd.it` URL and `None` for empty/`None` input.
5. **Comment wording**: the new fleet entries are labelled sibling-reported rather than
   "verified working", because this repository cannot verify instance liveness offline.

## Verification

| Check | Result |
|---|---|
| `python -m compileall -q "testing area" tests .github/scripts` | clean |
| `python tests/test_smoke.py` | `SMOKE TEST: ALL PASS` — 1157 PASS, 0 FAIL |
| `python tests/test_reddit_signals.py` | `ALL PASS (96 pass)` |
| `python tests/test_twitter_media.py` | `ALL PASS` |
| `pyflakes` on the engine, before vs after | identical (only the two pre-existing unused `global current_run_stats` notices) |
| production-shaped checkout (`sync_prod.sync_tree`, no `README.md`/`docs/`) | `SMOKE TEST: ALL PASS` — 1152 PASS (the README/docs-only checks are skipped there by design) |

Invariants held: single-page cards stay byte-identical (no `📜 Page 1/1`), multi-page cards
stay under Discord's 4000-character limit, `💬`/`👍` are still never fabricated when stats are
hidden, and the mixed-media card renders two galleries rather than merging photo and video
into one row.

## Limits

- No network in CI: the three new Redlib hosts and their post-page behaviour are
  sibling-reported. The suite proves fleet shape, ordering, exclusion, and the wave
  partition — not live reachability.
- No live Reddit run was performed from here. The end-to-end cases are mocked contracts
  (`resolve_post_media` with mocked `fetch_arctic_post` / `enrich_gallery_redlib` /
  `resolve_video_url`), the same style as rounds 47, 60, and 74 in this repository.
- The ID-only crosspost hydration costs **one extra Arctic lookup per post**, and only when
  the parent has no path; it is deliberately not attempted when the path is already known.
- `docs/` and `README.md` never reach `uesu/7jkxmy9nvbc` and `uesu/wvkhabh2s22`, so the
  documentation changes here are development-repository only. The engine and test changes
  reach production through `sync_prod.yml` after merge.
