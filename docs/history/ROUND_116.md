# Round 116 — unwrap link-only Reddit tables for Discord (2026-11-13)

Scope: a narrow correction in the existing Reddit Markdown-table formatter, with one offline
regression. No relay intake, Discord component layout, link target, body policy, or other table
formatting behavior changes.

## Evidence

The supplied example's relay body ends with a one-column table exported by Reddit's rich-text editor:

```markdown
|[All Previous Showcase Megathreads](https://www.reddit.com/...)|
|:-|
```

This is a header cell followed by an alignment row, but there are no data rows. The formatter
previously left it untouched because it only converts a table when it has at least one data row.
Discord does not render Markdown tables, so the raw boundary pipes and `|:-|` can show in the card.
The test-channel screenshot shows that literal output; the proposed payload demonstrates the desired
clean link.

## Correction

When a valid one-column link header is immediately followed by a valid separator and no data rows,
remove the table wrapper and separator, leaving the Markdown link as its own line. Existing plain
header-only tables, malformed shapes, normal tables with data rows, and all other Markdown remain
byte-identical. Link text and target are preserved.

## Regression

`tests/test_smoke.py` covers the exact Showcase Megathreads link shape, its placement between prose
paragraphs, and the guard that a plain `|H|` plus `|:-|` is still unchanged.
