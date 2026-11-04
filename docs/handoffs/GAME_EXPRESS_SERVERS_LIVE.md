# Hand-off — Game-Express feature 4: third card "Servers Live" + actual End Time

**For:** the `uesu/Game-Express` maintainer session (dev repo → prod `uesu/8mqzv4k2n7c` via its
own `sync_prod.yml`). **From:** News-Express, 2026-11-04. **Base:** Game-Express `main` @
`f2c0cac4` (PR #144) — the patch was generated on that commit and re-applied on a fresh clone of
it with `git am --3way` (no conflicts). Engine + tests + docs only; no workflow `run:` block, no new
setting, no new secret. The complete patch is next to this file:
[`game-express-servers-live.patch`](game-express-servers-live.patch) (`git am`-able, 18 files,
+870/−32).

## 1. What it adds

Feature 4 posted two cards per version (`Pre-Load Started`, `Maintenance Started`). The patch adds
the third one, **`[SHORT - VERSION] Servers Live`**, on the same per-game webhook and ping, with
the version's locked launch media (the tier-1 launch video when the maintenance card has it) and
`Date Time` + `Hour Time` (`<t:…:R>`), and it **rewrites the `Maintenance Started` card's
`End Time`** from the scheduled clock (e.g. `11:00 AM`) to the moment the servers actually
reopened (silent `PATCH`, no re-ping).

The launcher is deliberately *not* a signal: HoYoPlay flips `main.tag` to the new version at
maintenance **start** (that is why the GI 7.2 maintenance card received its launch video at
07:00 while the servers were still down). "Live" therefore comes from two sources only:

| # | Signal | Games | Provenance |
|---|---|---|---|
| 1 | The publisher's completion notice / tweet — `Version 7.2 update maintenance has been completed`, `Update Completion Notice`, `servers are now online`, `… can now log in` (a stated clock such as `completed at 10:42 (UTC+8)` wins over the post time) | all | `official` |
| 2 | The HoYoverse client maintenance gate `getGlobalApplicationMaintenance`: `data.application_maintenance` is an object while servers are closed and `null` once they reopen; the flip is accepted only after the flag was seen **set** for that version | GI / HSR / ZZZ | `observed` (one-line note on the card until an official notice upgrades it silently) |

Guards (all tested): accepted only inside `[maintenance start + 20 min, + 24 h]`; only for a
`Maintenance Started` card this install posted itself; once per version; a non-zero `retcode`,
missing key or wrong shape is *unknown* and changes nothing; a `null` never preceded by a set
flag never posts; versions joined midway are seeded `live` together with `maintenance`; the gate
is never read outside the window (0 requests on idle days); the corrected `End Time` is marked
`end_actual` so later runs never restore the scheduled time. `REPOST=<game>:<version>:live`
re-sends one card on demand; `preview --kind maintenance` renders `maintenance_<game>_live`.

Wuthering Waves has no public gate, so it uses signal 1 only (Kuro news / `@Wuthering_Waves`);
HNA and ANANTA stay out of feature 4 as before.

## 2. Sources behind the third card

| Source | URL | Role |
|---|---|---|
| seriaati / hoyo-update-notifier | https://github.com/seriaati/hoyo-update-notifier (live at https://hun.seria.moe/) | Reference implementation of the gate: endpoint per game, headers `x-rpc-app_version` / `x-rpc-client_type: 1` / `x-rpc-cg_game_biz`, `game_biz` values, the "maintenance has started / is over" state machine (`hun/utils.py`, `hun/scheduler.py`); already credited in Game-Express for the Sophon branches endpoint |
| yeci226 / ZZZ | https://github.com/yeci226/ZZZ (`src/utilities/news/sources.ts`) | Independent production reader of the same gate; cross-check of the response shape (`application_maintenance: object \| null`, anything else = unknown) and of the Star Rail gateway host |
| HoYoverse maintenance gate (GI / HSR / ZZZ) | `https://sg-cg-api.hoyoverse.com/hk4e_global/cg/gamer/api/getGlobalApplicationMaintenance` · `https://cg-hkrpg-api.mihoyo.com/hkrpg_cn/cg/gamer/api/getGlobalApplicationMaintenance` · `https://sg-cg-nap-api.hoyoverse.com/nap_global/cg/gamer/api/getGlobalApplicationMaintenance` | Signal 2 (`gamexpress/sources/launcher.py::MAINT_STATUS`); Star Rail's global cloud gateway is the shared `hkrpg_cn` host in both references — HoYoverse maintains every region in one window |
| HoYoPlay branches | `https://sg-hyp-api.hoyoverse.com/hyp/hyp-connect/api/getGameBranches?launcher_id=VYTpXlbWo8` | Already used; now also yields `live_tag` (`7.2.0`) for the gate's `x-rpc-app_version` header |
| HoYoLAB official notices (gid 2 / 6 / 8) | `https://bbs-api-os.hoyolab.com/community/post/wapi/getNewsList?gids=<gid>&type=1` → `getPostFull` | Signal 1 for GI / HSR / ZZZ (same feed that supplies the maintenance notice) |
| Kuro official news (WuWa) | `https://hw-media-cdn-mingchao.kurogame.com/akiwebsite/website2.0/json/G152/en/{ArticleMenu,MainMenu}.json` → `article/<id>.json` | Signal 1 for Wuthering Waves |
| Official X accounts via the Nitter fleet | existing `sources/twitter.py` instances | Signal 1 corroboration ("update maintenance has been completed, … can now log in") |
| Discord webhook `PATCH` | https://discord.com/developers/docs/resources/webhook#edit-webhook-message (with `with_components=true`) | The silent `End Time` correction and the observed → official upgrade |

Existing feature-4 sources (HoYoPlay `getAllGameBasicInfo`, Kuro launcher `G153` index and
`background/<hash>/en.json`, DynamiByte / Twintail / TomyJan launcher research) are unchanged and
already documented in Game-Express `docs/SOURCES.md` and `docs/CREDITS.md`; the patch adds the
gate row to SOURCES and the hun.seria.moe / yeci226 lines to CREDITS.

## 3. Files in the patch

`gamexpress/maintenance.py` (`live` milestone, `_resolve_live_signal`, `_correct_maintenance_end`,
`LIVE_WINDOW_S`, `LIVE_MIN_DOWNTIME_S`, `end_actual`), `gamexpress/schedule.py`
(`MAINT_COMPLETE_RE` + clause check, `maintenance_completed`, `extract_completion`,
`maint_completed_ts`), `gamexpress/sources/launcher.py` (`MAINT_STATUS`,
`parse_maintenance_status`, `hoyoplay_maintenance_status`, `live_tag`), `gamexpress/cards.py`
(`kind="live"`), `gamexpress/__main__.py` (preview sample), `tests/test_maintenance_live.py`
(13 cases) + `tests/test_smoke.py` (`parse_branches` expectation), `.github/workflows/ci.yml` and
`python_version_bump.yml` (new suite), `README.md` §4 + badge, `docs/CONFIGURATION.md`,
`docs/SOURCES.md`, `docs/CREDITS.md`, `docs/README.md` (anchor), `docs/changelog/*`,
`docs/PYTHON_VERSION.md`, `docs/PROD-REPO-SETUP.md`.

The README badge and the two doc sentences still said Python **3.14.8** while every workflow pins
**3.14.10** (the bump workflow never stages README or `docs/` on purpose); the patch refreshes
them — the only non-feature change.

## 4. Verification

- `tests/test_maintenance_live.py` 13/13, `tests/test_smoke.py` 610/610, the seven other offline
  suites green, `ruff check` clean — on the patch commit and again after `git am --3way` on a fresh
  clone of `f2c0cac4`.
- Not possible from here: a live read of the gate (host not reachable from the sandbox). First
  live confirmation = HSR 4.7 (~11 Nov) / WuWa 3.8 (~12 Nov, notice path only). If the gate
  never reports *set* during a maintenance, the card simply waits for the official notice — the
  design has no clock fallback.

## 5. Apply

```
git fetch origin && git checkout -b feature4-servers-live origin/main
git am --3way docs/handoffs/game-express-servers-live.patch   # from a News-Express checkout
python tests/test_maintenance_live.py && python tests/test_smoke.py
```
