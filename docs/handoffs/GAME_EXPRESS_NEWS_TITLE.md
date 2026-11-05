# Game-Express hand-off — news header: multi-line article titles render as one link (2026-11-05)

Scope: Game-Express `gamexpress/cards.py` (render only), one smoke test, changelog. No source,
HTML, media, state, workflow or setting change. Base: Game-Express `main` `959705b1`
(after #145). Patch next to this file: [`game-express-news-title.patch`](game-express-news-title.patch)
(`git am --3way`, no conflicts; GE smoke 611/611, ruff clean).

## Live case — HoYoLAB 47327567 (Honkai: Nexus Anima, `Game-Express Monitor #4297`)

The article's subject is two sentences separated by a **newline** inside the title string:

```
"A special teaser featuring Nexergy's Ambassadors for all Animasters.\nJoin them anytime, anywhere, and get some Nexergy!"
```

`news_payloads` wrote it verbatim into the header `## [title](url)`, so the link label spanned two
lines. Discord does not render a markdown link whose label contains a line break — the card showed
the raw `[A special teaser … Animasters.` / `Join them … Nexergy!]` / `(https://www.hoyolab.com/…)`
(see the delivered JSON in the run log: `"## [A special teaser … Animasters.\nJoin them … Nexergy!](https://www.hoyolab.com/article/47327567)"`).
Body, media, buttons and the HoYoLAB page itself were fine.

## Change

- `cards._md_link_text(s)` — the existing link-label helper (brackets → parentheses) now also
  collapses every whitespace run (newlines, tabs, ideographic spaces) to one space and strips.
- `news_payloads` builds the header title through `_md_link_text(strip_invisible(item.title))`
  instead of the inline bracket replace. `program_title` (schedule) and the beta name links already
  used the helper; single-line text is byte-identical through it.
- The source title (`item.title`, state hashes, dedupe) is untouched — the rule lives in the renderer.

Result for 47327567: `## [A special teaser featuring Nexergy's Ambassadors for all Animasters. Join them anytime, anywhere, and get some Nexergy!](https://www.hoyolab.com/article/47327567)`.

## Tests

`tests/test_smoke.py::test_news_title_with_a_newline_renders_as_one_line_link` (the live subject;
helper cases for `\r\n`, tabs, U+3000; the item's title keeps its newline). The ZZZ 47154012 pin
now expects the subject's stray trailing space stripped from the label (same rule).

## Apply

```
git checkout -b news-title-one-line origin/main
git am --3way docs/handoffs/game-express-news-title.patch   # (copied from News-Express)
python tests/test_smoke.py
```
