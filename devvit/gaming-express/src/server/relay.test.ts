import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {test} from 'node:test'
import {
  bareId,
  bootKey,
  CONTENT_BUDGET,
  classifyStatus,
  failKey,
  isDiscordWebhook,
  legacySeenKey,
  parseEnabled,
  parseSubreddits,
  parseUsers,
  type RelayRecord,
  seenKey,
  sortOldestFirst,
  toContent,
  toWebhookBody,
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
  // relayed on every 2-minute poll (observed 2026-11-01 14:21→14:27 PHT).
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

test('settings defaults: the twelve subreddits and five official accounts parse untouched', () => {
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
  assert.deepEqual(parseUsers(users), [
    'genshinimpact',
    'HonkaiStarRail',
    'ZZZ_Official',
    'HonkaiNexusAnima',
    'AnantaOfficial',
  ])
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
