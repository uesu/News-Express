# X (Twitter) poll media in monitor cards

This guide documents the poll handling in the active Twitter V3 monitor (`testing area/twitter_v3.py` and `testing area/twitter_proxy.py`). It applies to the Twitter monitor only; it does not change Reddit or the Devvit relay.

## What the card shows

When poll data is available, the card renders each option's label and percentage (or vote count when no percentage is available), plus the total votes and remaining time when the provider supplies them. If X exposes poll-choice artwork, the images appear in the existing media gallery after the post's ordinary photos, GIFs, or videos. The existing card layout and action buttons are unchanged; the monitor does not add vote buttons.

For the supported X poll-card bindings, the lookup considers choices by their original choice index and prefers X's original-resolution rendition. Other available variants are fallbacks. The image URLs are passed through to Discord; the monitor does not download or probe the image files itself.

## When the image lookup runs

Tweet providers sometimes return poll results without per-choice image URLs. When a tweet has a poll with choices and one or more choice images are missing, the monitor makes one conditional GET to X's public syndication endpoint:

`https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en&token={token}`

The token follows the formula used by Vercel's open-source [`react-tweet` fetcher](https://github.com/vercel/react-tweet/blob/main/packages/react-tweet/src/api/fetch-tweet.ts). The response's poll card bindings are matched by choice index so images do not slide onto the wrong option. A poll that already has all choice URLs and an ordinary non-poll tweet skip this extra request. This is a one-time enrichment during post processing, not a vote-refresh request.

VxTwitter's `pollData` is normalized into the monitor's common poll representation (labels, counts, percentages, totals and timing when present). The fallback does not manufacture image URLs when that provider has none.

## Fallback and freshness behavior

If the syndication request times out, returns a non-success status, does not match the requested tweet, has no usable poll image bindings, or X does not expose the artwork, the monitor continues with the poll's text/results and posts without choice art. It does not fail the whole tweet because optional image enrichment was unavailable.

Poll results are a snapshot from the provider response when the post is processed. The monitor does not periodically refresh vote counts or edit an old post as votes change. The existing posted-ID cache and delivery behavior remain in effect.

## Verification record

The offline `tests/test_twitter_media.py` suite covers token calculation, the conditional request, indexed choice extraction and original-resolution preference over 420px thumbnails, enrichment without mutating the source tweet, graceful no-art behavior, card action/layout preservation, and gallery order with ordinary media. The CI smoke workflow runs this suite. For PR #156, the syndication response was also probed against [a real HonkaiNA poll](https://x.com/HonkaiNA/status/2125077752852500587) and returned all three choice-image URLs. The original Bobabirb image was checked locally at 3072 × 3072 and approximately 1.10 MB. That proves the returned original image is accessible at that size; offline payload tests do not substitute for a new live Discord post using the original URLs.

## Related sources

- [Vercel `react-tweet` token reference](https://github.com/vercel/react-tweet/blob/main/packages/react-tweet/src/api/fetch-tweet.ts)
- [X syndication response example](https://cdn.syndication.twimg.com/tweet-result?id=2125077752852500587&lang=en&token=55g4mqlsrg1hi)
- [Example poll post](https://x.com/HonkaiNA/status/2125077752852500587)
- [Implementation and tests in PR #156](https://github.com/uesu/News-Express/pull/156)
