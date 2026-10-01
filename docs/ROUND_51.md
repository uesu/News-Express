# Round 51 — profile crossposts, vxReddit shell handling, and repository audit (2026-10-02)

## Purpose

This record documents the October 2 maintenance change and the accompanying
repository-wide review. It is deliberately kept with the code so the behavior,
validation, active workflow, configuration impact, and policy review are all
reviewable from Git history rather than only from an Actions log or PR comment.

## 1. Behavior changed

### Profile-origin crossposts render as profiles

`testing area/reddit_main_v3.py` now distinguishes a profile-origin crosspost
from an ordinary subreddit-origin crosspost before rendering the Components V2
header. All of these permalink forms are recognized:

| Original permalink form | Card line |
|---|---|
| `/user/<name>/comments/...` | `🔁 Crosspost of [u/<name>](https://www.reddit.com/user/<name>/) Profile` |
| `/u/<name>/comments/...` | same canonical profile line |
| `/r/u_<name>/comments/...` | same canonical profile line |

The destination is deliberately the canonical `https://www.reddit.com/user/<name>/`
profile URL rather than a post-specific or pseudo-subreddit alias. Existing
`/r/<subreddit>/comments/...` output, the notice-only subreddit fallback, and
all media/original-post lookup behavior are unchanged.

### Generic vxReddit shell is a miss, not post metadata

`testing area/reddit_proxy.py` now rejects a vxReddit response only when both
conditions hold:

1. it contains no extracted media; and
2. its `og:title`, after trimming and case normalization, is exactly
   `vxreddit`.

That exact response is the generic mirror shell observed for some crosspost
permalinks. Treating it as a fetch miss lets the established proxy/native
fallback continue and prevents the shell title from reaching a Discord card.
A page with actual media remains accepted even if it uses that title, and other
titles retain their previous behavior.

### Cached test tweet is observable without changing deduplication

The active Twitter workflow executes `testing area/twitter_v3.py`. When its
manual `TEST_TWEET_ID` input maps to an existing `<account>_<tweet_id>` entry
in `posted_tweets.json`, it still takes the normal `continue` path and cannot
post the tweet a second time. It now logs that this is an intentional,
cache-protected skip. The standby V2 card script receives the same diagnostic
for parity; workflow routing remains V3 and was not changed.

## 2. Regression coverage

`tests/test_smoke.py` remains an offline, no-secret, no-network suite and now
pins these contracts:

* each of `/user/`, `/u/`, and `/r/u_` profile-crosspost paths renders the
  clean canonical profile Markdown;
* the existing ordinary subreddit-crosspost fixture remains the legacy
  regression check;
* a whitespace/case variant of a media-less `vxReddit` title is rejected;
* the same title with a real `og:image` remains usable; and
* V2 and V3 both retain the cache `continue` after adding the visible
  `TEST_TWEET_ID` skip diagnostic.

CI already compiles all Python sources and runs this suite plus
`tests/test_reddit_signals.py` on pull requests.

## 3. Repository-wide tracking review

The audit was performed against the current GitHub `main` on October 2, 2026.
`main` had advanced by two commits since this branch point, both deleting
obsolete screenshot binaries. Those commits were merged into the branch before
this record was written, so the PR diff contains neither image restoration nor
an unrelated binary change.

The 43 tracked upstream paths reviewed were:

| Area | Tracked paths reviewed | Result |
|---|---|---|
| Root configuration and state | `.env.example`, `.gitignore`, `requirements.txt`, `pending_reddit.json`, `posted_reddit.json`, `posted_tweets.json`, `proxy_health.json` | Cache files are intentionally ignored for normal local edits and force-added by the monitor workflows; their documented schema/retention and dedup use remain accurate. The test-tweet wording in `.env.example` now explains the intentional cache skip. |
| Root project and policy docs | `README.md`, `PRIVACY_POLICY.md`, `TERMS_OF_SERVICE.md` | README release history and test-tweet instructions are updated. No data category, recipient, retention period, credential handling, or acceptable-use term changed, so the Privacy Policy and Terms require no artificial effective-date update. |
| GitHub automation | `.github/dependabot.yml`, `.github/workflows/ci.yml`, `.github/workflows/dependabot_auto_merge.yml`, `.github/workflows/python_version_bump.yml`, `.github/workflows/reddit_monitor.yml`, `.github/workflows/twitter_monitor.yml` | CI already covers compile + both offline suites. The active monitor targets Reddit V3 and Twitter V3; no workflow, secret, permission, schedule, or repository Variable change is required for this patch. |
| Existing documentation | `docs/CI_SMOKE.md`, `docs/DEPENDABOT.md`, `docs/DISCOHOOK.md`, `docs/DOCS_PATCH_ROUNDS_42_45.md`, `docs/PR_ROUNDS_42_44.md`, `docs/PYTHON_RUNTIME.md`, `docs/ROUND_46.md`, `docs/ROUND_46B.md`, `docs/ROUND_49.md`, `docs/ROUND_49_REPLAY_TESTS.md`, `docs/ROUND_50.md`, `docs/bump_3.14.8.patch`, `docs/round-15-validation.md`, `docs/round_46b.patch` | These are retained historical/operator records. Round 51 is the new authoritative record for this change. |
| Monitor and helper Python | `testing area/reddit_main.py`, `testing area/reddit_main_v2_embedez.py`, `testing area/reddit_main_v3.py`, `testing area/reddit_proxy.py`, `testing area/reddit_signals.py`, `testing area/twitter_proxy.py`, `testing area/twitter_v1.py`, `testing area/twitter_v2_button_outside.py`, `testing area/twitter_v3.py`, `testing area/video_diag.py` | Only Reddit V3, its proxy helper, active Twitter V3, and the V2 parity copy change. Older engines were reviewed but intentionally left untouched. |
| Automated tests | `tests/fixtures/posted_cards.py`, `tests/test_reddit_signals.py`, `tests/test_smoke.py` | The smoke suite is extended for this behavior; the independent Reddit signal suite needs no change because no signal/gate semantics changed. |

With this document added, the delivered tree has 44 tracked paths before any
future workflow cache commit. Python bytecode remains ignored; no generated
artifact or credential was added.

## 4. Validation performed

Before publishing the PR update:

```text
python -m py_compile "testing area/reddit_main_v3.py" "testing area/reddit_proxy.py" \
  "testing area/twitter_v2_button_outside.py" "testing area/twitter_v3.py"
python tests/test_smoke.py
python tests/test_reddit_signals.py
git diff --check
```

The smoke suite additionally uses deterministic in-memory fake proxy responses;
no live Reddit, vxReddit, X, Discord, or webhook call is made by these checks.
