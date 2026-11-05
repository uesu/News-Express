# Game-Express hand-off — X: link / app card artwork is not tweet media (2026-11-05)

Companion to News-Express Round 110 ([`docs/history/ROUND_110.md`](../history/ROUND_110.md)).
Scope: Game-Express `gamexpress/sources/twitter.py::_fx_media` (one filter), one smoke test,
changelog. No render, state, workflow or setting change. Base: Game-Express `main` `959705b1`
**on top of the news-title patch** `778a8a8a` (apply that one first — the changelog README's
"Latest" line chains on it). Patch next to this file:
[`game-express-card-artwork.patch`](game-express-card-artwork.patch) (`git am --3way`; GE smoke
612/612, every other `tests/test_*.py` green, ruff clean).

## Why GE is exposed

FxTwitter folds an X link / app card's artwork into the tweet's `media.photos` list. HonkaiNA
2118221775108771936 (photo) and 2118191579307381245 (video) carry an App Store card, and both
list `https://pbs.twimg.com/card_img/2117885179226374144/8O4A5wKA?format=png&name=orig` (the
512 × 512 app icon) next to the real 1920 × 1080 photo / 1280 × 720 video. `_fx_media` reads
`photos` first and `sane_aspect(512, 512)` passes, so the icon is handed on as `item.images` and
can reach a schedule card (`images[:4]`) or a notice card (`notice_images = images[:1]`) — for a
video tweet it is even the **first** image because photos come before videos.

## Change

- `_is_card_art(url)` — `pbs.twimg.com/card_img/…` only; native photos are `/media/…`, videos
  `video.twimg.com`.
- `_fx_media` returns the native entries when any exist; a card-only tweet (a link card's banner)
  keeps its artwork exactly as before. Order of the native entries is unchanged.

News-Express does the equivalent on its side (the card art becomes the Discord card's Section
thumbnail, since NE renders the tweet itself); GE only uses tweet images as key art, so dropping
the card art is the whole fix there.

## Tests

`tests/test_smoke.py::test_fx_media_ignores_card_artwork_when_the_tweet_has_its_own_media` —
photo + card, card + video, card-only kept, two photos around a card, empty media, classifier
negatives (`/media/`, `video.twimg.com`, a look-alike host, `None`).

## Apply

```
git checkout -b x-card-artwork origin/main
git am --3way docs/handoffs/game-express-news-title.patch     # if not already merged
git am --3way docs/handoffs/game-express-card-artwork.patch   # (both copied from News-Express)
python tests/test_smoke.py
```
