# Round 109 — Inline image interleaving for self-posts (2026-11-04)

Scope: the card builder only — `build_v3_payload` in `testing area/reddit_main_v3.py` plus
five small helpers next to the round-62 scrub. Touch-ups to the Components v2 layout; no new
card format, no change to discovery, liveness, caches, workflows or the Devvit relay. Applies to
every subreddit, crossposts and continuation pages alike because the single choke point
(`_drop_gallery_media_lines` → quotes → tables → budget split) is unchanged and the new marking
step sits directly in front of it.

## Live case — `Zenlesszonezeroleaks__1xnbsam` "Gachabase Update!" (run #12499)

A self-post whose author embedded thirteen pictures *inside* the prose, Reddit-style:

```
# 1 - Revision Timeline

[https:\/\/zzz.gachabase.net\/timeline](https://preview.redd.it/uy4q028a2izh1.png?…)

You can now view any version …

# 2 - Gallery https://preview.redd.it/sn8hetth2izh1.png?…

and the ability to compare images too https://preview.redd.it/zevtfvgj2izh1.png?…
```

The card rendered as one 2,207-character text block with every raw `preview.redd.it` URL still
glued to its heading, the first caption as a link whose text kept Reddit's escaped `\/` and
whose target was the picture, and all thirteen pictures in one trailing gallery (10 + 3, split
over two containers) **in proxy order** — the first tile was section 9's picture. The round-62
scrub only removes a line that is *nothing but* the URL, so a URL at the end of a heading or a
captioned link stayed.

## What changed

### `_mark_inline_gallery_images(body, photo_media)` — runs before the choke point

Every in-body reference to a **gallery photo** becomes an invisible token line
(`⁣IMG<n>⁣`, `n` = index into the photo list, U+2063 INVISIBLE SEPARATOR as the fence):

| body form | result |
|---|---|
| bare `https://preview.redd.it/…` / `https://i.redd.it/…` (anywhere on a line) | URL removed, token line inserted |
| `[caption](https://preview.redd.it/…)` / `![alt](…)` | caption kept as plain text with `\/` and markdown escapes restored, token line inserted |
| `[same-picture-url](same-picture-url)` or empty caption | token line only |
| a second reference to the same picture | removed, no token |
| link/URL to a picture that is **not** in the gallery | byte-identical |

Identity is `_reddit_media_key` (so the body's `preview.redd.it/<id>.png?…` matches an
`i.redd.it/<id>.png` gallery rendition, as in round 62). A body with no gallery reference is
returned byte-identical, so nothing downstream can change for the ordinary post.

### `_inline_img_segments(body_out)` — reading order

The budgeted first-page text is split at the token lines into `(text, [pictures])` segments.
The interleaved layout is used only when **some picture follows prose** (a token after
non-blank text). The round-62 case (the body is only the picture URL) and a picture-first
body with a caption below it keep the legacy layout (text above the gallery), with the inline
URL scrubbed.

### The interleaved card

```
header
text ₁ / gallery ₁ (its pictures, body order)
text ₂ / gallery ₂
…
gallery (pictures the text never references, old order, ≤10 per gallery)
gallery (video tile — round 38c, unchanged)
stats line / divider / buttons
```

- `_pack_v2_containers(units, accent)` packs *units* (a section's text + its gallery; the
  stats / divider / buttons trio) into ≤10-child containers so a heading is never separated
  from its picture by a container break; every container keeps the orange accent.
- `_count_v2_components` counts every component (containers, children, buttons). Over the
  40-component cap the last two sections fold into one (prose joined, pictures pooled) until
  the message fits — 14 one-picture sections fit as is, 30 become 13 + one pooled section.
- A picture referenced only on a continuation page (round 66 budget split) joins the trailing
  gallery of the main card; `_strip_inline_img_tokens` removes tokens (and any split-damaged
  fragment) from the remainder and from both legacy branches, so no token can reach Discord.
- Header, stats line, `Page n/N` suffix, divider, action row, accent, tombstone handling
  (`tombstone_payload` prepends to the first container) and the 4,000-character text budget
  are untouched; text totals can only shrink.

Result for 1xnbsam: three containers (9 / 10 / 6 children, 31 components), nine sections in
post order with their own picture, the caption rendered as `https://zzz.gachabase.net/timeline`
plain text, the three pictures the (truncated) body never mentioned in a trailing gallery.

## Guards

`tests/test_smoke.py` `r109`: the live shape (reading order, URL scrub, caption unescape,
trailing gallery), unchanged header/stats/buttons/accent, no token leak, legacy card
byte-identical for an unreferenced body, round-62 URL-only body, picture-first body,
non-gallery links kept, duplicate references, i.redd.it rendition match, video tile placement,
>10 trailing pictures, continuation-page pictures, 12/14/20/30-section cap folding, and the
call-order pin inside `build_v3_payload`.

## Game-Express

Game-Express renders its Reddit cards with its own builder (`gamexpress/cards.py`); the
inline-image scrub/interleave is a News-Express card concern. The hand-off comment on the
PR carries the News-Express diff for reference so the same reading-order rule can be applied
there if a GE Reddit card shows the same symptom.
