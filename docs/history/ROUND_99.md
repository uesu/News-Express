# Round 99 (2026-10-31) — megathread format corrections + why REDLIB-REACH reads 0/26

## Provenance

1. **Live card `HonkaiStarRail_leaks/1xkgd9m`** ("How could the General Question and
   Discussion Megathread hit 100k", image post with a long body, delivered 17:40Z to the
   test webhook). Eight operator screenshots compared three renderings of the same text:

   | Source | Spoiler-format example | "Previous Megathreads" block |
   |---|---|---|
   | Discord card (as delivered) | `>Spoiler Topic` / `>\|\|spoiler tagged text here` / a dark spoiler box swallowing the line break + `separate paragraph of spoiler tagged text\|\|` — one broken spoiler spanning two lines, no quote bar | raw `\|Previous Megathreads\|`, `\|:-\|`, `\|Latest Megathread - September 27- October 31\|`, `\| All Previous Megathreads\|` |
   | reddit.com | three blockquotes whose text is the **literal** `\>!spoiler tagged text here!<` (the author escaped the opener to *show* the syntax) | a one-column table: header *Previous Megathreads*, two link rows |
   | Arctic Shift raw Markdown | `>Spoiler Topic` / `>\>!spoiler tagged text here!<` / `>\>!separate paragraph of spoiler tagged text!<` | `---`, `\|Previous Megathreads\|`, `\|:-\|`, `\|[Latest Megathread](…HonkaiStarRail\_leaks…) - September 27- *October 31*\|`, `\| [All Previous Megathreads](…)\|` |

2. **The approved target** — the operator's hand-corrected Components V2 payload
   (`polishing and refining/7jkxmy9nvbc live prod reddit repo format correction or addition.txt`):

   ```
   > Spoiler Topic
   > >!spoiler tagged text here!<
   > >!separate paragraph of spoiler tagged text!<
   …
   ---

   Previous Megathreads

   [Latest Megathread](https://www.reddit.com/r/HonkaiStarRail\_leaks/comments/1wquywn/…) - September 27 - October 31

   [All Previous Megathreads](https://www.reddit.com/r/HonkaiStarRail_leaks/?f=flair_name%3A%22Megathread%22)
   ```

   Links, URLs (including the `\_` escapes inside them), wording and media are **not**
   altered by this round — format only. (The reference also hand-typed `September 27 -
   October 31`; the engine keeps the source cell `September 27- *October 31*` verbatim.)

3. **Production logs `Reddit Feed Monitor #11934` (15:31Z) and `#11982` (19:30Z)**: both
   print `REDLIB-REACH: 0/26 instance(s) answered this run` with every mirror at `0/1`
   (#11982) or `0/2` (#11934), plus `redlib gallery enrichment failed (all instances)` on
   every delivered post. The whole 26-instance sweep completed in ~7 s — the mirrors were
   *answering*, just not with a post page.

## Root cause — the card

The body of an image+text post never comes from RSS (the feed item carries only the image),
so this card's text came from the plain-Markdown path (`_clean_plain_body` →
`_normalize_reddit_markdown`). Two gaps there, one at the card build:

1. **Escaped spoiler openers were converted anyway.** `_REDDIT_SPOILER_RE` matched the
   `>!…!<` inside `\>!spoiler tagged text here!<`, producing `>\||spoiler tagged text
   here||`. Discord then read `\|` as an escaped pipe, leaving a stray `|`, and paired the
   remaining `||` with the next line's — hence the spoiler box that ate the line break.
   The HTML path already kept such text literal (`r16 blockquote` / `r41 megathread
   spoiler policy` guards); the Markdown path now agrees.
2. **`>text` is a blockquote on Reddit, a literal `>` on Discord.** Reddit does not
   require the space; Discord does. The line was passed through unchanged.
3. **One-column tables were invisible.** `_split_markdown_table_row` required ≥ 2 cells,
   so `|Previous Megathreads|` / `|:-|` were never recognised as a table and the raw pipe
   rows reached the card.

## What changed (engine: `testing area/reddit_main_v3.py`)

### `_normalize_reddit_markdown` (plain-Markdown path only)

- `\>!text!<` → literal `>!text!<` (the backslash is swapped for a private marker before
  the spoiler pass and restored as a bare `>!`; Discord has no `>!` syntax, so the literal
  is safe and matches the approved card). A real `>!x!<` on the same line still becomes
  `||x||`; code spans are still skipped.
- A quote line written without the space gains it: `>Spoiler Topic` → `> Spoiler Topic`;
  `>\>!x!<` → `> >!x!<`; `>#### Head` → `> **Head**`. `> already spaced`, an unconverted
  `>!` opener, `plain >not quote` and fenced code are untouched. `>>nested` flattens to one
  level, exactly as the HTML path's `_apply_quote_markers` already does.

### `_format_quote_blocks` (new, card-build choke point, every body source)

Blank lines **between two quote lines** are dropped, so consecutive quote paragraphs render
as one Discord quote block (the approved shape). Blank lines next to prose, inside fenced
code, and all non-blank lines are byte-identical. Wired as
`_format_markdown_tables(_format_quote_blocks(_drop_gallery_media_lines(...)))` — still one
call site, still identical for RSS / FULL MODE / Arctic / proxy bodies.

### `_format_markdown_tables` — one-column tables, boundary-piped rows

- `_split_markdown_table_row` accepts a **single** cell only when the line carries both
  boundary pipes (`|cell|`, closing pipe unescaped). Prose with a pipe (`Suoming | 5*
  Electro Sword`), `|only` and `only` are not rows; a lone `|only|` line, or a header +
  separator with no data row, still converts nothing (round-71 "never guess" intact, all
  `_r66_bad_tbls` and the round-71 fixtures unchanged).
- A one-column table renders as a titled list — the heading line, a blank line, then each
  row's cell on its own line separated by blank lines (no `- heading: value` bullets:
  there is no second column to label). Multi-column tables keep the round-71 row blocks.
- `_table_row_indices` lets blank lines sit **between two boundary-piped rows** (Reddit's
  rich-text editor exports blank lines between table rows just as it does between list
  items — the live Discord card showed every row as its own paragraph). A blank line never
  bridges to prose or to an unbounded pipe line; a contiguous table walks `i, i+1, …` as
  before, so the malformed/glued rules see exactly what they saw in round 71.

### Result for `1xkgd9m` (both the contiguous and the blank-line-separated source shapes)

```
> Spoiler Topic
> >!spoiler tagged text here!<
> >!separate paragraph of spoiler tagged text!<

**We recommend checking out the below useful resources:**
…
---

Previous Megathreads

[Latest Megathread](https://www.reddit.com/r/HonkaiStarRail\_leaks/comments/1wquywn/pearlgpt\_feed\_this\_megathread\_to\_the\_voracity/) - September 27- *October 31*

[All Previous Megathreads](https://www.reddit.com/r/HonkaiStarRail_leaks/?f=flair_name%3A%22Megathread%22)
```

Applies to every future post (the rules are generic; nothing is keyed to this thread).

## Root cause — `REDLIB-REACH: 0/26`

Investigated against upstream on 2026-10-31 (GitHub API, `redlib-org/redlib` and
`redlib-org/redlib-instances`):

| Date | Event | Effect on the monitor |
|---|---|---|
| 2026-10-20 ~18:40Z | Reddit starts answering anonymous **comments/thread JSON** with an HTML 403 (redlib#591). Listings still work. | Every Redlib **post page** renders *"Failed to parse page JSON data"*. The reach probe fetches post pages, `_is_redlib_error_page` correctly rejects the 200 error page → `0/1` on every stock mirror. |
| 2026-10-22 | **v0.40.0** released (`ba116c11`, still the latest release and the last commit on `main`). | Contains **no** post-page fix: the fixes are unmerged PRs — #603 (GraphQL comments), #599 (shreddit HTML scraper) — plus community forks (polak14, xevxx, knguyen1, MiningTcup/redlib-ng). |
| 2026-10-27 | redlib#604 "Currently working Redlib instances" lists thepixora, r.naa.gg, nadeko, r4fo, catsarch, reallyaweso.me, miningtcup, freedit, utilibre — **all already in the fleet**. | — |
| 2026-10-29 | Reddit begins blocking anonymous JSON **listings** too ("Redlib is currently unusable", #603 thread). The official instance list drops from 11 (Oct 23) to **2** (Oct 29) and 3 (Oct 31: `redlib.cow.rip`, `redlib.privadency.com`, one onion). A TLS-fingerprint switch is reported as a temporary workaround on individual hosts. | Even listing-only reserves stop answering → `0/26` in #11934 / #11982. |
| 2026-10-30 | redlib#609: Reddit's Q3 shareholder letter announces a move to a **logged-in-only** Reddit (tests in Q4). | The outage is structural, not transient. |

So `0/26` is **not an engine or fleet defect**: the error-page/no-DOM detection from round
83c is doing its job, and the 7-second sweep shows the mirrors are up but cannot serve a
post. Nothing the monitor delivers depends on Redlib alone (proxy services and native media
carried both runs; `redlib gallery enrichment failed` is the documented benign line).

### Fleet decision

- **No Redlib release newer than 0.40.0**, and no commit on `main` since 2026-10-22.
- `redlib.privadency.com` (official list) is already seat 16. `redlib.cow.rip` is the only
  clearnet host in the official list that the fleet lacks, and the README records it as
  **deliberately excluded** for its Cloudflare interstitial — that decision stands; with
  post pages broken upstream it would read `0/1` anyway. `reddit.rtrace.io` appeared in the
  list on Oct 25–27 and was gone again by Oct 29. No fleet change this round.

### What the engine now tells you (`REDLIB-REACH-WHY`)

The probe used to swallow every failure (debug-level log, bare `except: pass`), so a 0/26
line could not distinguish a datacenter block from an upstream error page. Round 99 tallies
each miss by class — `error-page:<round-83c marker>`, `no-post-dom` (challenge/splash),
`http-<status>`, `non-html`, `empty-body`, `timeout`, `exc:<ExceptionName>` — and logs one
extra line right after `REDLIB-REACH:` when anything missed, most frequent first:

```
REDLIB-REACH-WHY: error-page:failed to parse page json data ×22, http-403 ×3, timeout ×1
```

Zero extra requests; `log_redlib_reachability()` still **returns only** the `REDLIB-REACH:`
line, so `reddit_run_result.json`, the workflow summary step (14.7 KB, unchanged) and the
round-86/95 summary guards are untouched. `_is_redlib_error_page` is now a thin wrapper over
`_redlib_error_marker` (same marker list, same verdicts). The tally is per-run state,
cleared with `_redlib_reach`.

Expected reading once upstream ships a post-page fix and instances update: the
`error-page:failed to parse page json data` count falls and `REDLIB-REACH` climbs on its
own; a dominant `no-post-dom` / `http-403` instead would mean the runner is being
challenged/blocked and is the signal to re-rank.

## Verification

```
python3 tests/test_smoke.py           # SMOKE TEST: ALL PASS (1309 PASS, 0 FAIL)
python3 tests/test_reddit_signals.py  # REDDIT SIGNAL TEST: ALL PASS (103 pass)
python3 tests/test_twitter_media.py   # TWITTER MEDIA TEST: ALL PASS
```

New guards (`r99: …`): the live body renders as the approved card (contiguous and
blank-line-separated table shapes), escaped-vs-real spoilers on one line, quote spacing
cases, `_format_quote_blocks` boundaries, one-column detection limits with all round-66/71
fixtures re-asserted, the choke-point wiring, and the REDLIB-REACH-WHY tally (counting
unchanged, log-only, per-run, most-frequent-first) with a scripted seven-host probe.

## Limits

- Discord rendering was verified against the operator's approved payload and the engine's
  text output, not by a live post from this branch.
- The escaped-opener rule covers `\>!` only (the live shape); an escaped closer alone
  (`>!x!\<`) is still read as a spoiler.
- Proxy bodies that arrive as raw Reddit Markdown (vxReddit's `og:description` is the
  post's `selftext`) still bypass `_normalize_reddit_markdown`; they only reach the card
  when the base body is empty and that service wins media, and they do receive the
  choke-point quote merge and table rendering. Not changed here — out of this round's scope.
