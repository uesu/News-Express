import assert from 'node:assert/strict'
import {test} from 'node:test'
import {
  CONTENT_BUDGET,
  classifyStatus,
  isDiscordWebhook,
  parseSubreddits,
  type RelayRecord,
  sortOldestFirst,
  toContent,
  toWebhookBody,
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
