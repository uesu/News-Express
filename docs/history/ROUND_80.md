# Round 80 — emoji outside link (Discord forward fidelity, 2026-10-23)

## Symptom

* `AnantaLeaks_1xd1tks` `"You'll never guess where the game starts😂"` delivered as `### [You'll never guess where the game starts😂](https://www.reddit.com/r/AnantaLeaks/comments/1xd1tks/…)` — in-channel OK, but **Forward to another channel** showed raw `([https://…/youll_never… ) *by` leak (screenshot 11:30 AM `News Test ANANTA APP`). Discord Components V2 `### [title](url)` is strict — emoji inside `[...]` breaks forwarding.
* User: emoji should be outside for **all future posts** — `[…😂]` not good.

## Fix

* `testing area/reddit_main_v3.py` only — `build_v3_payload` header `id:2`:
  * new `_clean_post_title` already normalizes title (`[:400]`, collapse ws, strip byline artifact);
  * new ` _is_emoji_char80` / `_split_trailing_emoji80` — peels trailing `So/Sk` + `ZWJ/VS/skin-tone/flag` sequences (`\u200d`, `\ufe0f`, `1F3FB–1F3FF`, `1F1E6–1F1FF`, `20e3`) via `unicodedata.category`;
  * `### [{clean}]({url}) 😂\n*by …*` when suffix present, else original `### [{raw}]({url})\n*by …*`; empty-title guard keeps `😂`-only inside.

Original HTML/JSON/source bodies untouched — presentation-only, `0` extra req, no perf loss.

## Verification

* `python3 -m compileall -q "testing area" tests → compileall: OK`
* `timeout 120 python3 tests/test_smoke.py → SMOKE TEST: ALL PASS` (38 suites, emoji unit `starts😂→starts / 😂`, `😂-only` guard, full regression)
* Manual `#9496 1xd1tks (69.0 min latency, 65.0 min removal_notice)` → new header would be `### [You'll never guess where the game starts](…) 😂` — forward-safe.

## Deploy

No `.github/workflows` edit — attended path. Merge `arena/1a05c012-news-express` → manual upload `testing area/reddit_main_v3.py` + `tests/test_smoke.py` (+ docs) to `7jkxmy9nvbc`/`wvkhabh2s22` (engine first per `AGENTS.md`).

## References

PR #74 `f256b8c` (Round 79) + this PR; base `4c7833c`.
