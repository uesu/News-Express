import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {test} from 'node:test'
import {
  bareId,
  becameLive,
  bodyHash,
  bootKey,
  CONTENT_BUDGET,
  classifyStatus,
  dueStage,
  failKey,
  isDiscordWebhook,
  legacySeenKey,
  parseEnabled,
  parseSubreddits,
  parseUsers,
  RECHECK_STAGES_SECONDS,
  RECHECK_WINDOW_HOURS,
  type RelayRecord,
  seenKey,
  shouldReport,
  sortOldestFirst,
  spoilerChanged,
  stateKeyOf,
  toContent,
  toMultipartBody,
  toUpdateContents,
  toWebhookBody,
  type UpdateItem,
  uniqueById,
  userTarget,
} from './relay.ts'

function rec(over: Partial<RelayRecord> = {}): RelayRecord {
  return {
    v: 1,
    id: '1xkgd9m',
    sub: 'Genshin_Impact_Leaks',
    title: 'Luna III Megathread',
    permalink: '/r/Genshin_Impact_Leaks/comments/1xkgd9m/luna_iii_megathread/',
    url: 'https://www.reddit.com/r/Genshin_Impact_Leaks/comments/1xkgd9m/luna_iii_megathread/',
    created: 1793400000,
    author: 'AutoModerator',
    flair: 'Megathread',
    distinguished: null,
    spoiler: false,
    nsfw: false,
    score: 1,
    comments: 0,
    removed: null,
    xpost: null,
    media: [],
    body: '',
    bodyTruncated: false,
    ...over,
  }
}

function parseContent(content: string): RelayRecord {
  const m = /^```json\n([\s\S]*)\n```$/.exec(content)
  assert.ok(m, 'content is one fenced json block')
  return JSON.parse(m[1] as string) as RelayRecord
}

test('parseSubreddits: trims, strips r/, de-dups case-insensitively, rejects junk', () => {
  assert.deepEqual(
    parseSubreddits(
      ' r/AnantaLeaks, /r/Genshin_Impact_Leaks ,genshin_impact_leaks,, bad name!, HonkaiStarRail_leaks',
    ),
    ['AnantaLeaks', 'Genshin_Impact_Leaks', 'HonkaiStarRail_leaks'],
  )
  assert.deepEqual(parseSubreddits(undefined), [])
  assert.deepEqual(parseSubreddits(''), [])
})

test('parseSubreddits: the six production subreddits survive untouched', () => {
  const six =
    'AnantaLeaks,Genshin_Impact_Leaks,HonkaiNexusAnimaLeaks,HonkaiStarRail_leaks,WutheringWavesLeaks,Zenlesszonezeroleaks_'
  assert.deepEqual(parseSubreddits(six), six.split(','))
})

test('toContent: small record round-trips unchanged', () => {
  const r = rec({body: 'hello **world**', media: ['https://i.redd.it/a.png']})
  const out = toContent(r)
  assert.ok(out.length <= CONTENT_BUDGET)
  assert.deepEqual(parseContent(out), r)
})

test('toContent: an r/WutheringWaves "Official News" re-post keeps flair + distinguished through truncation', () => {
  // Kuro has no u/ publisher account; official Wuthering Waves content reaches
  // r/WutheringWaves as community re-posts under the "Official News" flair
  // (e.g. 1xd9vyy "Insider Channel: Special Program" by u/cakeel-, not
  // distinguished). Consumers classify from `flair`; `distinguished` is carried
  // for mod/admin notices and is null for these.
  const r = rec({
    sub: 'WutheringWaves',
    author: 'cakeel-',
    flair: ':YangyangSide: Official News',
    distinguished: null,
    body: 'y'.repeat(5000),
  })
  const back = parseContent(toContent(r))
  assert.equal(back.flair, ':YangyangSide: Official News')
  assert.equal(back.distinguished, null)
  assert.equal(back.author, 'cakeel-')
  assert.equal(back.bodyTruncated, true)
  assert.match(back.flair ?? '', /\bofficial\b/i)
  const mod = parseContent(toContent(rec({distinguished: 'moderator'})))
  assert.equal(mod.distinguished, 'moderator')
})

test('toContent: long body is truncated and flagged, identity fields intact', () => {
  const r = rec({
    body: 'x'.repeat(5000),
    media: ['https://i.redd.it/a.png', 'https://i.redd.it/b.png'],
  })
  const out = toContent(r)
  assert.ok(out.length <= CONTENT_BUDGET, `len ${out.length}`)
  const back = parseContent(out)
  assert.equal(back.bodyTruncated, true)
  assert.ok(back.body.endsWith('…'))
  assert.ok(back.body.length < 5000)
  assert.equal(back.id, r.id)
  assert.equal(back.permalink, r.permalink)
  assert.deepEqual(back.media, r.media)
})

test('toContent: media list shrinks before identity fields when everything is huge', () => {
  const media = Array.from(
    {length: 40},
    (_, i) => `https://i.redd.it/${'m'.repeat(60)}${i}.png`,
  )
  const r = rec({body: 'y'.repeat(3000), media})
  const out = toContent(r)
  assert.ok(out.length <= CONTENT_BUDGET, `len ${out.length}`)
  const back = parseContent(out)
  assert.ok(back.media.length < media.length)
  assert.equal(back.id, r.id)
  assert.equal(back.title, r.title)
})

test('toContent: unicode and json-escaped bodies stay within budget', () => {
  const r = rec({
    body: '"quoted" \\ back\n'.repeat(400) + '日本語テキスト'.repeat(200),
  })
  const out = toContent(r)
  assert.ok(out.length <= CONTENT_BUDGET, `len ${out.length}`)
  parseContent(out)
})

test('toWebhookBody: mentions are disabled', () => {
  const body = JSON.parse(toWebhookBody('@everyone <@&123>'))
  assert.deepEqual(body.allowed_mentions, {parse: []})
  assert.equal(body.content, '@everyone <@&123>')
})

test('isDiscordWebhook: only https discord.com webhook URLs', () => {
  assert.equal(
    isDiscordWebhook(
      'https://discord.com/api/webhooks/1547613015258439793/abcDEF_-123',
    ),
    true,
  )
  assert.equal(
    isDiscordWebhook(
      'https://discord.com/api/webhooks/1547613015258439793/abcDEF_-123/',
    ),
    true,
  )
  assert.equal(isDiscordWebhook('http://discord.com/api/webhooks/1/x'), false)
  assert.equal(
    isDiscordWebhook('https://discordapp.com/api/webhooks/1/x'),
    false,
  )
  assert.equal(isDiscordWebhook('https://evil.com/api/webhooks/1/x'), false)
  assert.equal(
    isDiscordWebhook('https://discord.com/api/channels/1/messages'),
    false,
  )
  assert.equal(isDiscordWebhook(''), false)
  assert.equal(isDiscordWebhook(undefined), false)
})

test('classifyStatus: 2xx ok, 429/5xx retry, other 4xx drop', () => {
  assert.equal(classifyStatus(200), 'ok')
  assert.equal(classifyStatus(204), 'ok')
  assert.equal(classifyStatus(429), 'retry')
  assert.equal(classifyStatus(502), 'retry')
  assert.equal(classifyStatus(400), 'drop')
  assert.equal(classifyStatus(401), 'drop')
  assert.equal(classifyStatus(404), 'drop')
})

test('sortOldestFirst: chronological and non-mutating', () => {
  const xs = [{created: 3}, {created: 1}, {created: 2}]
  assert.deepEqual(
    sortOldestFirst(xs).map(x => x.created),
    [1, 2, 3],
  )
  assert.deepEqual(
    xs.map(x => x.created),
    [3, 1, 2],
  )
})

test('devvit.json: secret settings carry no defaultValue (upload schema rule)', () => {
  // Reddit's config-file.v1.json rejects a GlobalStringSetting that has both
  // isSecret:true and defaultValue — `devvit upload` fails with
  // "settings.global.<key> is not exactly one from …". Guard it here so the
  // mistake is caught by `npm test` instead of at upload time.
  const cfgPath = new URL('../../devvit.json', import.meta.url)
  const cfg = JSON.parse(readFileSync(cfgPath, 'utf8')) as {
    settings?: {global?: Record<string, Record<string, unknown>>}
  }
  const globals = cfg.settings?.global ?? {}
  assert.ok(globals.intakeWebhook, 'intakeWebhook setting must exist')
  for (const [key, def] of Object.entries(globals)) {
    if (def.isSecret === true) {
      assert.equal(
        'defaultValue' in def,
        false,
        `${key}: secret settings must not define defaultValue`,
      )
    }
  }
})

test('redis keys: listing id (t3_x) and record id (x) map to the same marker', () => {
  // v0.0.1 defect: bootstrap/lookup keyed on `t3_1xkvvda`, the post-send
  // marker on `1xkvvda` — the marker never matched and the same post was
  // relayed on every poll (observed 2026-11-01 14:21→14:27 PHT on 2-minute polls).
  assert.equal(bareId('t3_1xkvvda'), '1xkvvda')
  assert.equal(bareId('1xkvvda'), '1xkvvda')
  assert.equal(seenKey('t3_1xkvvda'), seenKey('1xkvvda'))
  assert.equal(seenKey('1xkvvda'), 'seen:1xkvvda')
  assert.equal(failKey('t3_1xkvvda'), failKey('1xkvvda'))
  // The upgrade path still recognises markers written by v0.0.1.
  assert.equal(legacySeenKey('t3_1xkvvda'), 'seen:t3_1xkvvda')
  assert.equal(legacySeenKey('1xkvvda'), 'seen:t3_1xkvvda')
  assert.notEqual(legacySeenKey('1xkvvda'), seenKey('1xkvvda'))
})

test('parseUsers: strips u/ and user/, de-dups, keeps Reddit-legal names only', () => {
  assert.deepEqual(
    parseUsers(
      ' u/genshinimpact, /u/HonkaiStarRail ,honkaistarrail, user/ZZZ_Official, bad name!, ',
    ),
    ['genshinimpact', 'HonkaiStarRail', 'ZZZ_Official'],
  )
  assert.deepEqual(parseUsers(undefined), [])
  assert.deepEqual(parseUsers(''), [])
})

test('settings defaults: the twelve subreddits and three verified publisher accounts parse untouched', () => {
  const cfg = JSON.parse(
    readFileSync(new URL('../../devvit.json', import.meta.url), 'utf8'),
  ) as {
    settings: {global: Record<string, {defaultValue?: string}>}
    dev?: {subreddit?: string}
  }
  const subs = cfg.settings.global.subreddits?.defaultValue ?? ''
  const users = cfg.settings.global.officialUsers?.defaultValue ?? ''
  assert.equal(parseSubreddits(subs).length, 12)
  assert.deepEqual(parseSubreddits(subs), subs.split(','))
  // Game-Express sources (config/games.json → reddit.subreddits / reddit.official).
  for (const s of [
    'Genshin_Impact',
    'HonkaiStarRail',
    'ZZZ_Official',
    'WutheringWaves',
    'HonkaiNexusAnima',
    'AnantaOfficial',
  ])
    assert.ok(parseSubreddits(subs).includes(s), s)
  // Verified + active only (Arctic Shift audit 2026-11-02). u/ZZZ_Official (one post,
  // 2024-04) and u/AnantaOfficial (one post, 2024-12, removed) are dormant; their
  // official content is community re-posts under "Official Media" in their subreddit.
  assert.deepEqual(parseUsers(users), [
    'genshinimpact',
    'HonkaiStarRail',
    'HonkaiNexusAnima',
  ])
  for (const dormant of [
    'ZZZ_Official',
    'AnantaOfficial',
    'WutheringWaves',
    'WutheringWavesMod',
  ])
    assert.ok(
      !parseUsers(users).includes(dormant),
      `${dormant} must not be a default`,
    )
  // `devvit upload` from a fresh zip no longer tries to create a playtest subreddit.
  assert.equal(cfg.dev?.subreddit, 'gaming_express_dev')
})

test('parseEnabled: the CLI stores typed text, so "false" must pause too', () => {
  // v0.0.2 defect: `npx devvit settings set relayEnabled` → `false` was stored as the
  // string "false", `enabledRaw !== false` stayed true and the relay kept sending.
  for (const paused of [
    false,
    'false',
    'False',
    ' FALSE ',
    '0',
    'no',
    'off',
    'paused',
  ])
    assert.equal(parseEnabled(paused), false, String(paused))
  for (const on of [
    true,
    'true',
    'True',
    '1',
    'yes',
    'on',
    '',
    undefined,
    null,
  ])
    assert.equal(parseEnabled(on), true, String(on))
})

test('uniqueById: a post seen in both the u/ feed and the subreddit listing is sent once', () => {
  const xs = [
    {id: 't3_abc', sub: 'u_genshinimpact'},
    {id: 'abc', sub: 'Genshin_Impact'},
    {id: 'def', sub: 'Genshin_Impact'},
    {id: 'ABC', sub: 'Genshin_Impact'},
  ]
  assert.deepEqual(uniqueById(xs), [xs[0], xs[2]])
  assert.equal(userTarget('genshinimpact'), 'u/genshinimpact')
  assert.notEqual(
    bootKey(userTarget('HonkaiStarRail')),
    bootKey('HonkaiStarRail'),
  )
})

// ---------------------------------------------------------------------------
// 0.0.7 — complete record attachment + post-delivery re-check
// ---------------------------------------------------------------------------

function item(over: Partial<UpdateItem> = {}): UpdateItem {
  return {
    id: '1xlmk75',
    sub: 'Genshin_Impact_Leaks',
    age: 640,
    stage: 1,
    removed: null,
    deleted: false,
    edited: false,
    spoiler: false,
    nsfw: false,
    locked: false,
    score: 14,
    comments: 3,
    ...over,
  }
}

test('toContent: 0.0.7 optional fields round-trip and the media cut is flagged', () => {
  const r = rec({
    full: true,
    edited: false,
    xpostPermalink: '/r/Genshin_Impact/comments/1xl0000/parent/',
    video: {
      fallback: 'https://v.redd.it/abc/CMAF_1080.mp4?source=fallback',
      hls: 'https://v.redd.it/abc/HLSPlaylist.m3u8',
      gif: false,
    },
  })
  const back = parseContent(toContent(r))
  assert.equal(
    back.v,
    1,
    'post records stay v1 so pre-0.0.7 readers keep working',
  )
  assert.equal(back.full, true)
  assert.equal(back.xpostPermalink, r.xpostPermalink)
  assert.deepEqual(back.video, r.video)
  assert.equal(back.mediaTruncated, undefined)

  const huge = rec({
    media: Array.from(
      {length: 40},
      (_, i) =>
        `https://preview.redd.it/${'x'.repeat(40)}${i}.png?width=2048&s=${'s'.repeat(40)}`,
    ),
    body: 'b'.repeat(3000),
  })
  const cut = parseContent(toContent(huge))
  assert.ok(cut.media.length < 40 && cut.media.length > 0)
  assert.equal(
    cut.mediaTruncated,
    true,
    'readers fetch record.json when the inline list was cut',
  )
  assert.equal(cut.bodyTruncated, true)
})

test('toMultipartBody: payload_json + record.json in one hand-built form, boundary never inside the parts', () => {
  const full = {...rec({body: 'x'.repeat(5000), full: true}), parent: null}
  const content = toContent(full)
  const {body, contentType} = toMultipartBody(content, full)
  const boundary = /boundary=(.+)$/.exec(contentType)?.[1] as string
  assert.ok(boundary.startsWith('----GamingExpress'))
  const parts = body.split(`--${boundary}`)
  assert.equal(parts.length, 4, 'preamble, payload, file, closing')
  assert.ok(parts[3]?.startsWith('--\r\n'), 'closing delimiter')
  const payloadPart = parts[1] as string
  assert.match(payloadPart, /name="payload_json"/)
  const payload = JSON.parse(payloadPart.split('\r\n\r\n')[1]?.trim() as string)
  assert.equal(payload.content, content)
  assert.deepEqual(payload.allowed_mentions, {parse: []})
  assert.deepEqual(payload.attachments[0], {
    id: 0,
    filename: 'record.json',
    description: `relay record ${full.id} (complete)`,
  })
  const filePart = parts[2] as string
  assert.match(filePart, /name="files\[0\]"; filename="record.json"/)
  const file = JSON.parse(filePart.split('\r\n\r\n')[1]?.trim() as string)
  assert.equal(file.body.length, 5000, 'the attachment is never trimmed')
  assert.equal(file.bodyTruncated, false)
  assert.equal(
    parseContent(content).bodyTruncated,
    true,
    'while the inline record is',
  )
  assert.ok(!JSON.stringify(full).includes(boundary))
})

test('dueStage: five looks — 5 min, 30 min, 2 h, 6 h and 24 h', () => {
  assert.equal(RECHECK_WINDOW_HOURS, 24)
  assert.deepEqual([...RECHECK_STAGES_SECONDS], [300, 1800, 7200, 21600, 86400])
  assert.equal(dueStage(0), 0)
  assert.equal(dueStage(299), 0)
  assert.equal(dueStage(300), 1)
  assert.equal(dueStage(1799), 1)
  assert.equal(dueStage(1800), 2)
  assert.equal(dueStage(7200), 3)
  assert.equal(dueStage(21600), 4)
  assert.equal(dueStage(86399), 4)
  assert.equal(dueStage(86400), 5)
  assert.equal(dueStage(172799), 5)
  assert.equal(dueStage(172800), 5)
  assert.equal(dueStage(999999), 5)
})

test('becameLive: removed/filtered/deleted before and live now = approval', () => {
  const live = item({stage: 2, removed: null, deleted: false})
  assert.equal(becameLive(null, live), false, 'no earlier state known')
  assert.equal(becameLive(stateKeyOf(item({removed: null})), live), false)
  assert.equal(
    becameLive(stateKeyOf(item({removed: 'automod_filtered'})), live),
    true,
  )
  assert.equal(becameLive(stateKeyOf(item({removed: 'moderator'})), live), true)
  assert.equal(
    becameLive(stateKeyOf(item({removed: 'deleted', deleted: true})), live),
    true,
  )
  assert.equal(
    becameLive(
      stateKeyOf(item({removed: 'moderator'})),
      item({removed: 'moderator'}),
    ),
    false,
    'still removed',
  )
})

test('spoilerChanged: only a known post-level spoiler transition requests a complete re-send', () => {
  assert.equal(
    spoilerChanged(null, true),
    false,
    'first observation is not a transition',
  )
  assert.equal(spoilerChanged(stateKeyOf(item({spoiler: false})), false), false)
  assert.equal(spoilerChanged(stateKeyOf(item({spoiler: false})), true), true)
  assert.equal(spoilerChanged(stateKeyOf(item({spoiler: true})), false), true)
  assert.equal(
    spoilerChanged('removed=null|deleted=false', true),
    false,
    'unknown state fails closed',
  )
})

test('a re-sent record carries `resent` and `revision` inline', () => {
  const inline = parseContent(toContent(rec({resent: 'approved', revision: 2})))
  assert.equal(inline.resent, 'approved')
  assert.equal(inline.revision, 2)
})

test('shouldReport: the first look is always sent, later looks only when the state changed', () => {
  const first = item({stage: 1})
  assert.equal(shouldReport(first, stateKeyOf(first)), true)
  const same = item({stage: 2, score: 99, comments: 40})
  assert.equal(
    shouldReport(same, stateKeyOf(item({stage: 1}))),
    false,
    'score/comment drift is not a change',
  )
  const removed = item({stage: 2, removed: 'moderator'})
  assert.equal(shouldReport(removed, stateKeyOf(item())), true)
  const deleted = item({stage: 3, deleted: true, removed: 'deleted'})
  assert.equal(shouldReport(deleted, stateKeyOf(removed)), true)
  assert.equal(
    shouldReport(item({stage: 4}), null),
    true,
    'unknown previous state is reported',
  )
})

test('toUpdateContents: v2 batched messages that fit the budget, split only when needed', () => {
  const one = toUpdateContents([item()], 1793590000)
  assert.equal(one.length, 1)
  const m = /^```json\n([\s\S]*)\n```$/.exec(one[0] as string)
  assert.ok(m)
  const msg = JSON.parse(m[1] as string)
  assert.equal(msg.v, 2)
  assert.equal(msg.kind, 'update')
  assert.equal(msg.at, 1793590000)
  assert.deepEqual(msg.posts, [item()])

  const many = toUpdateContents(
    Array.from({length: 60}, (_, i) =>
      item({id: `1xlm${i.toString(36).padStart(3, '0')}`}),
    ),
    1793590000,
  )
  assert.ok(many.length > 1)
  let total = 0
  for (const c of many) {
    assert.ok(c.length <= CONTENT_BUDGET, `batch within budget (${c.length})`)
    total += JSON.parse(
      (/^```json\n([\s\S]*)\n```$/.exec(c) as RegExpExecArray)[1] as string,
    ).posts.length
  }
  assert.equal(total, 60, 'no item lost across batches')
})

test('bodyHash: stable, short, and sensitive to edits', () => {
  assert.equal(bodyHash('hello'), bodyHash('hello'))
  assert.equal(bodyHash('hello').length, 8)
  assert.notEqual(bodyHash('hello'), bodyHash('hello.'))
  assert.notEqual(bodyHash(''), bodyHash(' '))
})
