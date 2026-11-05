# Round 110 — Twitter: link / app card artwork becomes the card's thumbnail (2026-11-05)

Scope: `testing area/twitter_v3.py` card builder only (`build_v3_payload`, `build_quote_components`
and three small helpers). No feed, fetch, heal, cache or workflow change.

## Live case — HonkaiNA 2118221775108771936 (photo) and 2118191579307381245 (video)

Runs `Twitter Feed Monitor #13585` / `#13573`. Both tweets carry an **App Store app card**
("Honkai: Nexus Anima · Adventure · Open") under their media. FxTwitter folds that card's
artwork into the tweet's media list as one more photo — in both delivered payloads the second
gallery item is `https://pbs.twimg.com/card_img/2117885179226374144/8O4A5wKA?format=png&name=orig`,
a 512 × 512 PNG (the app icon), identical in both tweets because it is the same card. The builder
took FxTwitter's photos/videos verbatim, so the icon rendered as a full gallery tile next to the
real 1920 × 1080 photo / 1280 × 720 video. (The video tile looking black at first is the cold
Discord video proxy before playback — MEDIA-HEAL checked it and found nothing to fix.)

## What changed

- `is_card_image_url(url)` — X card artwork only ever lives under `pbs.twimg.com/card_img/…`;
  native tweet photos live under `/media/`, videos under `video.twimg.com`.
- `split_card_thumbnail(items)` — the **first** card image becomes the thumbnail **only when
  native media is present**; a card-only tweet keeps its gallery tile exactly as before (a link
  card's banner belongs full-width). A second card image is never dropped — it stays in the
  gallery after the native media.
- `thumbnail_section(texts, thumb)` — a Components v2 **Section** (type 9) with ≤3 text displays
  and the artwork as its **thumbnail accessory** (type 11) — the shape Discord gives a link
  preview, and the look of the server's Guidebook card.
- `build_v3_payload`: the Section holds the header line(s) (`… just tweeted:`, or the repost pair),
  the reply line when present, and the opening text chunk while a slot is free; remaining chunks
  follow full-width, then divider / gallery (native media only) / notes / quote / stats / divider /
  buttons as before. An article card already leads with its cover (`lead_gallery_items`), so it
  keeps no Section and the card image returns to the gallery ahead of the native media.
- `build_quote_components`: a quoted post with native media + card gets the same thumbnail beside
  its quote head.
- Everything else is byte-identical: card-only, photo-only, video-only, GIF and media-less tweets,
  translations, article cards, notes, stats and buttons. The round-47/49 heal walker already
  inspects Section accessories; the default `video` heal scope never edits for an image thumbnail.
  Text budget unchanged (the Section's text displays are the same components, re-homed).

## Guards

`tests/test_twitter_media.py` `r110`: URL classifier, photo + card and video + card shapes, legacy
shapes for card-only / photo-only / media-less, repost + reply slot filling, second card image kept,
article-cover case, quoted post thumbnail, heal walker visibility and Section text hygiene.

## Game-Express

`gamexpress/sources/twitter.py::_fx_media` reads the same FxTwitter `photos` list first, so a tweet
with a photo + app card hands GE `[photo, card icon]` and the icon can reach a schedule / notice
card (`item.images[:4]`, `[:1]`). Hand-off patch on the PR: ignore `/card_img/` photos when the
tweet has native media (card-only tweets unchanged), with a test.
