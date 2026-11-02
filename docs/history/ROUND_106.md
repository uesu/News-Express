# Round 106 — SyntaxWarning in the production log (2026-11-02)

## Symptom

Every production run of `uesu/7jkxmy9nvbc` since Round 101 started with

```
/home/runner/work/7jkxmy9nvbc/7jkxmy9nvbc/testing area/reddit_main_v3.py:3346:
SyntaxWarning: "\_" is an invalid escape sequence. Such sequences will not work in
the future. Did you mean "\\_"? A raw string is also an option.
```

(seen in the owner's logs of #12260 / #12262, the runs that delivered the first live
relay card `Genshin_Impact_Leaks_1xlvju8`).

## Cause

Compile-time only. The Round 101b docstring of `_unescape_markdown_in_urls` quotes the
live example `minmyouk\_xx` and the escape `` `\_` `` inside a normal (non-raw) triple-quoted
string. Python warns when it parses the file; the function body, the regexes and the card
output are untouched — nothing in a run behaved differently. The runner is on Python 3.12
(SyntaxWarning); Python 3.11 reports the same thing as a DeprecationWarning that is hidden
by default, which is why the local suites never showed it. A future Python turns invalid
escapes into a `SyntaxError`, i.e. the monitor would stop importing.

## Fix

- `testing area/reddit_main_v3.py`: the docstring is now a raw string (`r"""…"""`) with a
  one-line note; the text reads the same. No behavioural change.
- `tests/test_smoke.py` — `r106`: every `.py` under `testing area/`, `tests/` and
  `.github/scripts/` is compiled with all warnings recorded; any `SyntaxError`,
  `SyntaxWarning` or `DeprecationWarning` fails the suite with file:line. Verified to fail
  on the pre-fix file (`reddit_main_v3.py:3345: invalid escape sequence '\_'`) on 3.11 and
  to pass on the fixed tree.

## Verification

`python3 tests/test_smoke.py` ALL PASS · `tests/test_reddit_signals.py` 102 pass ·
`tests/test_twitter_media.py` ALL PASS · the same suites inside a `sync_tree()` production
checkout · `python3 -W error -c "compile(open('testing area/reddit_main_v3.py').read(),'x','exec')"`
is clean.

## Live evidence reviewed in this round

Run #12262 (`reddit engine test 3.txt`): `INTAKE: relay ok — 1 record(s) for this engine
(9 in window, 1 page(s), newest 262 s, 9 re-checked, 0 completed from record.json)`;
`Genshin_Impact_Leaks_1xlvju8` → `relay record is complete — no archive, redlib or
reddit.com request for this post (proxies only)`; media `vxreddit` 5 items (embeddit and
redditez tied); `Verified live: 1`; `Feed fallback: not attempted (relay is the listing)`;
runtime 7 s; LATENCY 7.3 min after creation (relay poll ≤5 min + cron-job.org trigger still
at 10 min — the 5-minute trigger brings this under ~6 min).
