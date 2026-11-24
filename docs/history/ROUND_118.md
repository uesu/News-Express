# Round 118 — opt-in cached tweet retest and poll footer polish

## Problem

A manual `test_tweet` run bypasses Nitter and injects one selected X status into the normal V3 processing path, but its dedup cache is intentionally shared with ordinary runs. In production run 16338, `HonkaiNA/2125077752852500587` was already present in `posted_tweets.json`, so the manual request correctly logged `TEST_TWEET_ID is already in the posted cache — skipping by design` and did not produce a fresh Discord card. That protects against duplicate sends during normal operations, but made an intentional visual retest inconvenient.

The poll footer also showed the vote total and remaining time without a visual marker. The proposed Discord payload used `:scroll:`; webhook JSON does not expand shortcode aliases, so the implementation uses the actual Unicode scroll emoji, `📜`.

## Changes

- Add a separate `force_test_tweet` boolean to the manual `workflow_dispatch` form and map it to `FORCE_TEST_TWEET`. It defaults off; an ordinary dispatch or scheduled run continues to respect the cache.
- When explicitly enabled, bypass dedup only for the one synthetic test entry matching the selected `TEST_TWEET_ID`, and only if that key existed in the cache at run start. An ordinary RSS entry can never use this override, and an uncached tweet cannot be posted twice because of the synthetic duplicate.
- Keep the cache key intact after a forced retest. A later scheduled run therefore still deduplicates the tweet. A successful forced delivery is reported in `forced_test_reposts` and the delivered count, not counted as a new candidate.
- Normalize a leading emoji/title boundary in each poll choice to include exactly one space (`🤎Bobabirb` → `🤎 Bobabirb`); preserve an existing space and keep joined emoji sequences intact.
- Prefix the compact poll-vote footer with the Unicode `📜` emoji and leave a blank line between option results and the footer. No poll/media/card actions or vote-refresh behavior changes.

## Guardrails and tests

Offline regressions prove the override requires the opt-in, the injected test-feed entry, a matching account/ID, and an ID cached before the run; ordinary feed entries, wrong IDs, and uncached items cannot force a cache bypass. Workflow tests verify the boolean input is opt-in and wired to the engine. Poll rendering tests verify emoji/title spacing, the blank-line footer and actual emoji glyph. The established cached-test skip remains the default and remains covered by smoke tests.

Run `python tests/test_twitter_media.py`, `python tests/test_smoke.py`, `python -m compileall -q 'testing area' tests`, and `git diff --check` before merge. The manual force option is intentionally not used by scheduled workflows; live Discord verification is a human-triggered action after the PR is reviewed and merged.

## Scope

Twitter V3 manual-test and poll-footer polish only. No Reddit, Devvit, cache schema, or default delivery behavior change.
