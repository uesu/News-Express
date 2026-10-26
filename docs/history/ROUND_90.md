# Round 90 (2026-10-26) — Multi-page `📜 Page X/Y` indicator, text-only proxy stats, and cross-page formatting preservation

## Provenance and scope

The maintainer relayed a verified patch package from the sibling Game-Express PR #71
comment ("apply this to new express") written against `uesu/News-Express` `main` @
`e77ebdb`, targeting `uesu/7jkxmy9nvbc` (Reddit production). It applies cleanly here
with only a line offset (this branch's round-89 test additions), and it lands as
**round 90** in this repository because `r88:` already names the 2026-10-25
full-body/Twitter-recovery round. The guard names were renamed accordingly; the
sibling's numbering was not kept.

Touched: `testing area/reddit_main_v3.py`, `testing area/reddit_proxy.py`,
`tests/test_smoke.py`, plus this record and the changelog/CI docs. No workflow,
Variable, Secret, scheduler, reminder/retraction-policy, dedup-cache or deployment
change. Nothing runs live from this repository.

## What changed

1. **Page indicator.** `build_v3_payload` appends ` • 📜 Page 1/N` to the stats
   line only when the body actually paginates; continuations gain a second `type: 10`
   component `-# 📜 Page n/N`. A bounded three-iteration fixed-point loop recomputes
   the page-1 budget from the footer length until the printed total equals
   `1 + len(build_continuation_payloads(rest))`.
2. **Text-only stats.** The `resolve_post_media` `else` branch (no usable proxy
   media — the common case for long text posts) now calls the same `_use_proxy_text()`
   helper as the media branches, so proxy-observed `💬`/`👍` counts are retained with
   zero extra HTTP requests and the RSS body is kept when non-empty.
   `fetch_proxy_post` records stats from the best-ranked responding wave and backfills
   them onto a text-only fallback result. Absent counts stay `None` (no zeros faked).
3. **Formatting.** `clean_rss_body` / `clean_proxy_body` preserve
   `<b>`/`<strong>` (with attributes), inline CSS `font-weight` spans, `<h1>`–`<h6>`,
   `<i>`/`<em>` and `<del>`/`<s>`/`<strike>`, trimming inner whitespace outside the
   markers and never double-wrapping. `_normalize_reddit_markdown` converts
   `####`–`######` subheadings to `**bold**` and native `>!spoiler!<` to `||spoiler||`
   outside code spans/fences. `_clean_selftext` replaces `strip_html` for JSON
   `selftext`, keeping paragraph breaks and Markdown while unescaping once.
4. **Split safety.** `_PROTECTED_SPAN_RES` also protects `~~…~~` and inline code;
   `split_card_body` and continuation chunking go through `_split_with_balance`, which
   closes an open fence (and reopens it with its info string) or the open inline
   marker and keeps each page within budget.

## Correction made to the relayed patch

The relayed `_clean_selftext` chose the HTML cleaner with a **tag allowlist**
(`div|p|br|table|ul|ol|li|blockquote|h1-6|strong|b|em|i`). Inputs using any other tag
fell through to the Markdown path, so `<pre><code>line1\nline2</code></pre>` and
`<span class="md-spoiler-text">secret</span>` rendered as **raw markup** in the card
(the old `strip_html` stripped them). The router now matches any HTML tag
(`</?[a-z][a-z0-9]*…>`), which restores the previous output for those shapes, keeps
autolink `<https://…>` and comparison text (`1 < 2`) on the Markdown path, and is
pinned by an `r90:` guard. This is the only behavioural deviation from the relayed
package.

The relayed `r66:` gallery-continuation guard was updated in place (payloads now
carry the footer component) with an inline note saying why, per the repository rule
that a changed guard is annotated rather than silently weakened.

## Verification (offline)

| Check | Result |
|---|---|
| `python3 -m compileall -q "testing area" tests .github/scripts` | clean |
| `python3 tests/test_smoke.py` | `SMOKE TEST: ALL PASS` (1131 PASS, 0 FAIL) |
| `python3 tests/test_reddit_signals.py` | `ALL PASS (96 pass)` |
| `python3 tests/test_twitter_media.py` | `ALL PASS` |
| 400 randomized bodies (2k–45k chars, with/without stats, with/without OP comment) | printed `Page 1/N` always equalled the real total; every payload under 4000; no `Page 1/1` on single-page posts |
| 300 randomized mixed Markdown documents (fences, bold/italic/strike, lists, inline code) | every continuation chunk ≤ 3800; even fence-marker count per page; no `****` artefact |
| 200 randomized short bodies vs the pre-round-90 engine | single-page payloads byte-identical; no body flipped between single- and multi-page |

These are offline unit/property checks with stubbed HTTP boundaries. They do not
certify Discord rendering or playback, and no production message, cache or
scheduler state was touched.

## Limits

- Page numbering is computed per build; a resumed delivery from `posted_messages.json`
  re-sends the stored payload/`N`, so a later source edit cannot renumber accepted
  pages.
- Stats retention depends on a proxy seeing the counts at fetch time; when Reddit
  hides scores, the card shows no counts by design.
- Formatting preservation is limited to the HTML/Markdown constructs listed above;
  arbitrary CSS, `<details>` and nested tables are not reinterpreted.
- Delivery of the extra footer component is untested against live Discord here; the
  first real multi-page post after merge should be confirmed on the production repo.
