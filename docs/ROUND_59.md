# Round 59 (2026-10-03) — nitter fleet body-audit

## Decision record

The three Twitter engines now use the same fallback order after reading each
host's actual `/Wuthering_Waves/rss` response body rather than trusting HTTP
status codes or homepage-probing trackers. No host was deleted:

1. `nitter.cf` and `xitter.cf` — the operator-approved primary pair.
2. `nitter.kareem.one` — body-verified feed; runs [shaquille's fork](https://git.kareem.one/shaquille/nitter).
3. `tw.eir-nya.gay` — body-verified feed; kitter, based on [Cynosphere's fork](https://gitlab.com/Cynosphere/nitter).
4. `nitter.meowing.monster` and `shitter.thepixora.com` — re-verified serving mirrors.
5. `nitter.miningtcup.me` — token-gated fallback (`NITTER_RSS_TOKEN`).
6. `nitter.netbub.com` and `nitter.jaydenha.uk` — retained as last-resort probes, but demoted because their RSS responses are challenge/interstitial pages.

Interstitial walls can return HTTP 200, so a valid feed requires real `<item>`
entries in the response body. The fleet is serial: tail entries cost nothing on
healthy runs and preserve automatic recovery if a wall is removed.

## Reddit fleet audit

The same body-read audit was applied to `/r/WutheringWavesLeaks/new.rss?limit=100`.
Native `reddit.com` remains the working primary and the optional token-backed
`redlib.miningtcup.me` contract is unchanged. Public candidates including
`redlib.kareem.one` and `teddit.net` were not added: they returned proof-of-work,
RSS-disabled, challenge, or no-response bodies. The existing Redlib tail is
kept and fails closed through permalink validation; no list change was made.

## Verification

The source fleet is pinned by smoke tests: operator pair in slots 1–2, both new
mirrors ahead of the token host, walled mirrors in the final two slots, and the
miningtcup token mapping unchanged. This record intentionally documents the
review without claiming network access from the development sandbox.
