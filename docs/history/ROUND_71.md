# Round 71 — Reddit Markdown-table readability

**Status:** In review — PR opened from `arena/316a205d-news-express`
**Scope:** Active Reddit V3 card body rendering (readability only)
**Date:** 2026-10-11
**Supersedes:** the round-66 table rendering (per-row `**bold-label**` bullets)

## Problem

Discord Components V2 has no native Markdown-table renderer. Round 66 already
detected a valid table and converted it, but the output was a per-row
`**bold-label**` block — every row repeated bold column headings, and nothing
separated one row from the next. On a phone a long release-schedule table read
as a wall of bold text.

This round is a **readability and formatting-quality improvement**. Reddit
delivery was never broken: the post is delivered, only the table's visual form
changes.

## Behavior

`_format_markdown_tables()` runs at the single card-build choke point, after
every source path (RSS, FULL MODE, Arctic Shift, proxy) has supplied the final
body — so all sources receive the identical readable form. A detected table is
rendered as compact, mobile-friendly grouped blocks:

```text
Patch 3.7
- Drip Market: August 25/26, 2026
- Beta Start: September 5, 2026
- Livestream: September 19, 2026
- First Half: October 2, 2026
- Second Half: October 23, 2026
- New Characters: Hsin and Suoming
```

* The first cell is the row's semantic key and is composed with its column
  heading when the cell does not already carry it (`Patch` + `3.7` →
  `Patch 3.7`; a cell that already says `Patch 3.8` is never doubled).
* One `- <column>: <value>` bullet per populated column; empty cells are
  skipped, and an empty first cell falls back to `Entry`.
* A blank line separates row blocks.
* HTML entities are decoded (`&amp;` → `&`).
* A `Q1:`-style line gains a blank line before it when it follows text, so a
  heading and its first question (`Frequently Asked Questions (FAQ):` /
  `Q1: Banners?`) do not run together.

Detection is unchanged from round 66 and deliberately conservative: a block
converts only when the header row is followed by a well-formed separator row of
the same width and a full run of data rows of that width. Malformed tables,
glued tables and ordinary prose containing a pipe (for example the live
`Suoming | 5\* Electro Sword` list lines) are returned byte-identical, and
nothing is date-converted — a range like `October 9/10` cannot become a
Discord timestamp without guessing, so the card's posted-time 🕐 stays the only
timestamp.

## Performance and safety

The transformation is local and linear in body length. It adds **no** provider,
proxy, media, cache, retry, or Discord request of any kind. Existing body and
total Components V2 text budgets remain in force, so the expanded formatted
output is still bounded before delivery, and the round-66 safe-split /
continuation pipeline operates on the formatted text exactly as before.

Reddit media handling, provider fallback, cache behavior, continuation
components, buttons, and YouTube previews are unchanged. The NSFW/content
policy position is unchanged (round 67 removed the content-advisory gate; this
round makes no content-based decision).

## Validation

```text
python -m compileall -q "testing area" tests
python tests/test_smoke.py
python tests/test_reddit_signals.py
git diff --check
```

The formatting regression checks cover the real live 1wxfuj5 table, grouped
patch blocks, entity decoding, FAQ spacing, the never-doubled label, escaped
pipes, empty cells/headers, and leaving ordinary pipe-containing prose and
malformed/glued tables byte-identical. The smoke suite passes 843/843
(838/838 before this round) and the signal suite 96/96.

## Not in this round

* No provider, request, retry, budget or cache behavior change.
* No date-to-Discord-timestamp conversion of body text.
* No change to media, galleries, videos, buttons or translation behavior.
