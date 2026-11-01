import type {IncomingMessage, ServerResponse} from 'node:http'
import {context, reddit, redis, settings} from '@devvit/web/server'
import type {
  PartialJsonValue,
  TriggerResponse,
  UiResponse,
} from '@devvit/web/shared'
import {
  bootKey,
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

// ---------------------------------------------------------------------------
// Tunables
// ---------------------------------------------------------------------------

/** Newest posts fetched per subreddit per poll. 2-min polls on leak subs
 *  never see more than a handful; 25 covers a burst with margin. */
const LISTING_LIMIT = 25
/** Hard cap on Discord sends per poll — the rest is picked up next tick. */
const MAX_SENDS_PER_POLL = 10
/** De-dup markers outlive the 48 h News-Express window by a wide margin. */
const SEEN_TTL_SECONDS = 7 * 24 * 3600
/** Give up on a post after this many delivery failures. */
const MAX_FAILS = 3
/** Per-request budget; the whole handler must finish well inside Devvit's
 *  30 s HTTP timeout. */
const DISCORD_TIMEOUT_MS = 8_000

type Endpoint =
  | 'internal/scheduler/poll'
  | 'internal/menu/poll-now'
  | 'internal/menu/status'
  | 'internal/on/app/install'

type PollResult = {
  subs: number
  users: number
  fetched: number
  bootstrapped: number
  sent: number
  skipped: number
  failed: number
  errors: string[]
}

// ---------------------------------------------------------------------------
// HTTP plumbing
// ---------------------------------------------------------------------------

export async function onReq(
  reqMsg: IncomingMessage,
  rspMsg: ServerResponse,
): Promise<void> {
  try {
    await route(reqMsg, rspMsg)
  } catch (err) {
    const msg = `server error; ${err instanceof Error ? err.stack : err}`
    console.error(msg)
    writeJson(500, {error: msg, status: 500}, rspMsg)
  }
}

async function route(
  reqMsg: IncomingMessage,
  rspMsg: ServerResponse,
): Promise<void> {
  const endpoint = (reqMsg.url ?? '')
    .replace(/^\//, '')
    .split('?')[0] as Endpoint
  if (reqMsg.method !== 'POST') {
    writeJson(404, {error: 'not found', status: 404}, rspMsg)
    return
  }
  switch (endpoint) {
    case 'internal/scheduler/poll': {
      const result = await runPoll()
      // Always 200: a failed send is retried next tick by design; a non-2xx
      // here would make the scheduler re-fire and double the Discord traffic.
      writeJson(200, {status: 'ok', ...result}, rspMsg)
      return
    }
    case 'internal/menu/poll-now': {
      const result = await runPoll()
      writeJson<UiResponse>(
        200,
        {
          showToast: {
            text: summarize(result),
            appearance: result.errors.length ? 'neutral' : 'success',
          },
        },
        rspMsg,
      )
      return
    }
    case 'internal/menu/status': {
      writeJson<UiResponse>(
        200,
        {showToast: {text: await statusText()}},
        rspMsg,
      )
      return
    }
    case 'internal/on/app/install': {
      console.log(
        `installed in ${context.subredditName ?? '?'} by ${context.username ?? '?'}`,
      )
      writeJson<TriggerResponse>(200, {}, rspMsg)
      return
    }
    default:
      writeJson(404, {error: 'not found', status: 404}, rspMsg)
  }
}

// ---------------------------------------------------------------------------
// The poll
// ---------------------------------------------------------------------------

async function runPoll(): Promise<PollResult> {
  const result: PollResult = {
    subs: 0,
    users: 0,
    fetched: 0,
    bootstrapped: 0,
    sent: 0,
    skipped: 0,
    failed: 0,
    errors: [],
  }
  const startedAt = Date.now()

  const [webhookRaw, subsRaw, usersRaw, enabledRaw] = await Promise.all([
    settings.get<string>('intakeWebhook'),
    settings.get<string>('subreddits'),
    settings.get<string>('officialUsers'),
    settings.get<boolean | string>('relayEnabled'),
  ])
  const webhook = (webhookRaw ?? '').trim()
  const enabled = parseEnabled(enabledRaw) && isDiscordWebhook(webhook)
  if (!isDiscordWebhook(webhook)) {
    result.errors.push(
      'intakeWebhook is empty or not a discord.com webhook URL — polling only',
    )
  }
  const subs = parseSubreddits(subsRaw)
  const users = parseUsers(usersRaw)
  result.subs = subs.length
  result.users = users.length
  if (subs.length === 0 && users.length === 0) {
    result.errors.push('no subreddits or official users configured')
    await redis.set('last:poll', JSON.stringify({at: startedAt, ...result}))
    return result
  }

  // 1. Fetch all listings concurrently: one call per subreddit (`/new`) and one
  //    per official account (`u/<name>` submitted, newest first). 12 + 5 calls
  //    every 2 minutes is well inside the 100 QPM budget.
  type Listing = {
    target: string
    sub: string | null
    posts: Awaited<ReturnType<typeof fetchSub>>
    error: string | null
  }
  const listings: Listing[] = await Promise.all([
    ...subs.map(async (sub): Promise<Listing> => {
      try {
        return {target: sub, sub, posts: await fetchSub(sub), error: null}
      } catch (err) {
        return {target: sub, sub, posts: [], error: describe(`r/${sub}`, err)}
      }
    }),
    ...users.map(async (user): Promise<Listing> => {
      const target = userTarget(user)
      try {
        return {target, sub: null, posts: await fetchUser(user), error: null}
      } catch (err) {
        return {target, sub: null, posts: [], error: describe(target, err)}
      }
    }),
  ])

  // 2. Bootstrap / de-dup.
  const candidates: RelayRecord[] = []
  for (const {target, sub, posts, error} of listings) {
    if (error) {
      result.errors.push(error)
      continue
    }
    result.fetched += posts.length
    const booted = await redis.get(bootKey(target))
    if (!booted) {
      // First poll for this target: remember everything, send nothing.
      // Prevents a 25-post flood into the intake channel on install or when
      // a subreddit / account is added to the settings.
      for (const p of posts)
        await redis.set(seenKey(p.id), '1', {expiration: ttl()})
      await redis.set(bootKey(target), `${startedAt}`)
      result.bootstrapped += posts.length
      continue
    }
    for (const p of posts) {
      if (await isSeen(p.id)) {
        result.skipped++
        continue
      }
      // Subreddit listings keep the configured spelling; a user-feed post is
      // labelled with the subreddit it was actually posted in (`u_<name>` for a
      // profile post), which is what the consumers key on.
      candidates.push(toRecord(p, sub ?? p.subredditName))
    }
  }

  // 3. Send oldest-first, once per id, bounded per poll.
  for (const rec of sortOldestFirst(uniqueById(candidates)).slice(
    0,
    MAX_SENDS_PER_POLL,
  )) {
    if (!enabled) {
      // Relay paused: remember the post so it is not sent later in a burst.
      await redis.set(seenKey(rec.id), 'paused', {expiration: ttl()})
      result.skipped++
      continue
    }
    const outcome = await deliver(webhook, rec)
    if (outcome === 'ok') {
      await redis.set(seenKey(rec.id), '1', {expiration: ttl()})
      result.sent++
    } else if (outcome === 'drop') {
      await redis.set(seenKey(rec.id), 'dropped', {expiration: ttl()})
      result.failed++
      result.errors.push(`${rec.id}: permanent Discord error — dropped`)
    } else {
      const fails = await redis.incrBy(failKey(rec.id), 1)
      await redis.expire(failKey(rec.id), SEEN_TTL_SECONDS)
      if (fails >= MAX_FAILS) {
        await redis.set(seenKey(rec.id), 'gave-up', {expiration: ttl()})
        result.errors.push(
          `${rec.id}: gave up after ${fails} transient failures`,
        )
      }
      result.failed++
    }
  }

  await redis.set(
    'last:poll',
    JSON.stringify({at: startedAt, ms: Date.now() - startedAt, ...result}),
  )
  await redis.incrBy('total:sent', result.sent)
  console.log(summarize(result))
  return result
}

function fetchSub(sub: string) {
  return reddit
    .getNewPosts({
      subredditName: sub,
      limit: LISTING_LIMIT,
      pageSize: LISTING_LIMIT,
    })
    .get(LISTING_LIMIT)
}

function fetchUser(user: string) {
  return reddit
    .getPostsByUser({
      username: user,
      sort: 'new',
      limit: LISTING_LIMIT,
      pageSize: LISTING_LIMIT,
    })
    .get(LISTING_LIMIT)
}

function describe(target: string, err: unknown): string {
  return `${target}: ${err instanceof Error ? err.message : err}`
}

/** De-dup lookup: current key spelling first, then the v0.0.1 spelling. */
async function isSeen(id: string): Promise<boolean> {
  if (await redis.get(seenKey(id))) return true
  return !!(await redis.get(legacySeenKey(id)))
}

function ttl(): Date {
  return new Date(Date.now() + SEEN_TTL_SECONDS * 1000)
}

// ---------------------------------------------------------------------------
// Post → record
// ---------------------------------------------------------------------------

function toRecord(
  p: {
    id: string
    title: string
    permalink: string
    url: string
    createdAt: Date
    authorName: string
    flair?: {text?: string} | undefined
    spoiler: boolean
    nsfw: boolean
    score: number
    numberOfComments: number
    removedByCategory?: string | undefined
    crosspostParentId?: string | undefined
    body?: string | undefined
    gallery: {url: string}[]
    secureMedia?:
      | {redditVideo?: {fallbackUrl?: string; hlsUrl?: string}}
      | undefined
  },
  sub: string,
): RelayRecord {
  const media: string[] = []
  const video = p.secureMedia?.redditVideo
  if (video?.fallbackUrl) media.push(video.fallbackUrl)
  else if (video?.hlsUrl) media.push(video.hlsUrl)
  for (const g of p.gallery ?? [])
    if (g?.url && !media.includes(g.url)) media.push(g.url)
  if (media.length === 0 && /\.(jpe?g|png|gif|webp|mp4)(\?|$)/i.test(p.url))
    media.push(p.url)

  return {
    v: 1,
    id: p.id.replace(/^t3_/, ''),
    sub,
    title: p.title,
    permalink: p.permalink,
    url: p.url,
    created: Math.floor(p.createdAt.getTime() / 1000),
    author: p.authorName,
    flair: p.flair?.text ?? null,
    spoiler: !!p.spoiler,
    nsfw: !!p.nsfw,
    score: p.score ?? 0,
    comments: p.numberOfComments ?? 0,
    removed: p.removedByCategory ?? null,
    xpost: p.crosspostParentId ?? null,
    media,
    body: p.body ?? '',
    bodyTruncated: false,
  }
}

// ---------------------------------------------------------------------------
// Discord
// ---------------------------------------------------------------------------

async function deliver(
  webhook: string,
  rec: RelayRecord,
): Promise<'ok' | 'retry' | 'drop'> {
  const body = toWebhookBody(toContent(rec))
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const rsp = await fetch(`${webhook}?wait=true`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body,
        signal: AbortSignal.timeout(DISCORD_TIMEOUT_MS),
      })
      const outcome = classifyStatus(rsp.status)
      if (outcome === 'ok') return 'ok'
      if (outcome === 'drop') {
        console.error(
          `[${rec.id}] Discord HTTP ${rsp.status}: ${(await rsp.text()).slice(0, 200)}`,
        )
        return 'drop'
      }
      if (rsp.status === 429 && attempt === 0) {
        const retryAfter = Number(rsp.headers.get('retry-after') ?? '1')
        await sleep(Math.min(Math.max(retryAfter, 0.5), 5) * 1000)
        continue
      }
      console.error(
        `[${rec.id}] Discord HTTP ${rsp.status} — will retry next poll`,
      )
      return 'retry'
    } catch (err) {
      console.error(
        `[${rec.id}] Discord request error: ${err instanceof Error ? err.message : err}`,
      )
      if (attempt === 0) {
        await sleep(1000)
        continue
      }
      return 'retry'
    }
  }
  return 'retry'
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// ---------------------------------------------------------------------------
// Status / helpers
// ---------------------------------------------------------------------------

function summarize(r: PollResult): string {
  const base = `poll: ${r.subs} subs, ${r.users} users, ${r.fetched} fetched, ${r.sent} sent, ${r.skipped} seen, ${r.failed} failed, ${r.bootstrapped} bootstrapped`
  return r.errors.length
    ? `${base}; ${r.errors.length} issue(s): ${r.errors[0]}`
    : base
}

async function statusText(): Promise<string> {
  const [last, total, subsRaw, usersRaw, enabledRaw, webhook] =
    await Promise.all([
      redis.get('last:poll'),
      redis.get('total:sent'),
      settings.get<string>('subreddits'),
      settings.get<string>('officialUsers'),
      settings.get<boolean | string>('relayEnabled'),
      settings.get<string>('intakeWebhook'),
    ])
  const subs = parseSubreddits(subsRaw)
  const users = parseUsers(usersRaw)
  const lastAt = last
    ? new Date(JSON.parse(last).at as number).toISOString()
    : 'never'
  return `last poll ${lastAt}; total sent ${total ?? 0}; ${subs.length} subs; ${users.length} users; relay ${parseEnabled(enabledRaw) ? 'on' : 'PAUSED'}; webhook ${isDiscordWebhook(webhook) ? 'set' : 'MISSING'}`
}

function writeJson<T extends PartialJsonValue>(
  status: number,
  json: Readonly<T>,
  rsp: ServerResponse,
): void {
  const body = JSON.stringify(json)
  rsp.writeHead(status, {
    'Content-Length': Buffer.byteLength(body),
    'Content-Type': 'application/json',
  })
  rsp.end(body)
}
