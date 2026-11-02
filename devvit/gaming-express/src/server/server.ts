import type {IncomingMessage, ServerResponse} from 'node:http'
import {context, reddit, redis, settings} from '@devvit/web/server'
import type {
  PartialJsonValue,
  TriggerResponse,
  UiResponse,
} from '@devvit/web/shared'
import {
  becameLive,
  bodyHash,
  bodyHashKey,
  bootKey,
  classifyStatus,
  dueStage,
  type FullRecord,
  failKey,
  isDiscordWebhook,
  isOfficialRecord,
  legacySeenKey,
  type OpComment,
  opCommentsHash,
  parseEnabled,
  parseSubreddits,
  parseUsers,
  type RelayRecord,
  SENT_ZSET,
  seenKey,
  shouldReport,
  sortOldestFirst,
  stageKey,
  stateKey,
  stateKeyOf,
  toContent,
  toMultipartBody,
  toUpdateContents,
  toWebhookBody,
  type UpdateItem,
  uniqueById,
  userTarget,
} from './relay.ts'

// ---------------------------------------------------------------------------
// Tunables
// ---------------------------------------------------------------------------

/** Newest posts fetched per subreddit per poll. 5-min polls (0.0.6; 2-min
 *  before) on leak subs never see more than a handful; 25 covers a burst. */
const LISTING_LIMIT = 25
/** Hard cap on Discord sends per poll — the rest is picked up next tick.
 *  15 at 5-minute polls (was 10 at 2-minute polls): same ceiling per minute. */
const MAX_SENDS_PER_POLL = 15
/** De-dup markers outlive the 48 h News-Express window by a wide margin. */
const SEEN_TTL_SECONDS = 7 * 24 * 3600
/** Give up on a post after this many delivery failures. */
const MAX_FAILS = 3
/** Per-request budget; the whole handler must finish well inside Devvit's
 *  30 s HTTP timeout. */
const DISCORD_TIMEOUT_MS = 8_000
/** 0.0.7: post-delivery re-checks (`reddit.getPostById`) per poll, and the
 *  wall-clock point after which a poll stops starting new work. */
const MAX_RECHECKS_PER_POLL = 20
const POLL_SOFT_DEADLINE_MS = 20_000
/** How long a delivered post stays on the re-check list (last stage + slack). */
const RECHECK_WINDOW_SECONDS = 86400 + 1800
/** 0.0.8: comments read per official post per re-check (author's own kept). */
const OP_COMMENTS_LIMIT = 50
/** After this many consecutive multipart failures the attachment is skipped
 *  for a while (plain JSON content only) so a Discord/Devvit quirk cannot
 *  double every send. */
const ATTACH_FAILS_BEFORE_PAUSE = 3
const ATTACH_PAUSE_SECONDS = 3600

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
  /** 0.0.7: posts re-checked after delivery, update messages sent, records
   *  re-sent because the body was edited. */
  rechecked: number
  updates: number
  resent: number
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
    rechecked: 0,
    updates: 0,
    resent: 0,
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
  //    per official account (`u/<name>` submitted, newest first). 12 + 3 calls
  //    every 5 minutes (3/min) is far inside the 100 QPM budget.
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
    const full = await completeRecord(rec, result)
    const outcome = await deliver(webhook, rec, full)
    if (outcome === 'ok') {
      await redis.set(seenKey(rec.id), '1', {expiration: ttl()})
      await rememberSent(rec)
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

  // 4. 0.0.7: look again at what was delivered (removals, deletions, edits;
  //    0.0.8: approvals and the publisher's own comments).
  try {
    await recheckDelivered(webhook, enabled, startedAt, result, users)
  } catch (err) {
    result.errors.push(describe('recheck', err))
  }

  await redis.set(
    'last:poll',
    JSON.stringify({at: startedAt, ms: Date.now() - startedAt, ...result}),
  )
  await redis.incrBy('total:sent', result.sent)
  console.log(summarize(result))
  return result
}

// ---------------------------------------------------------------------------
// 0.0.7: complete record + post-delivery re-check
// ---------------------------------------------------------------------------

/** Build the `record.json` payload: the untrimmed record plus the crosspost
 *  parent (one extra request, only for crossposts). Also fills
 *  `xpostPermalink` on the inline record. Never throws. */
async function completeRecord(
  rec: RelayRecord,
  result: PollResult,
): Promise<FullRecord> {
  const full: FullRecord = {...rec, parent: null}
  if (rec.xpost) {
    try {
      const parent = await reddit.getPostById(
        `t3_${rec.xpost.replace(/^t3_/, '')}`,
      )
      const parentRec = toRecord(parent, parent.subredditName)
      full.parent = parentRec
      rec.xpostPermalink = parentRec.permalink
      full.xpostPermalink = parentRec.permalink
    } catch (err) {
      result.errors.push(describe(`${rec.id} parent ${rec.xpost}`, err))
    }
  }
  return full
}

/** The post author's own comments under the post (0.0.8), oldest first.
 *  One request; failures are reported as "none" so a comment outage can
 *  never block the liveness update. */
async function authorComments(
  post: Awaited<ReturnType<typeof reddit.getPostById>>,
): Promise<OpComment[]> {
  try {
    const all = await post.comments.get(OP_COMMENTS_LIMIT)
    const author = post.authorName.toLowerCase()
    return all
      .filter(
        c =>
          c.authorName.toLowerCase() === author && (c.body ?? '').trim() !== '',
      )
      .map(c => ({
        id: c.id.replace(/^t1_/, ''),
        body: c.body ?? '',
        created: Math.floor(c.createdAt.getTime() / 1000),
        stickied: c.stickied,
      }))
      .sort((a, b) => a.created - b.created)
  } catch (err) {
    console.error(
      `[${post.id}] comments unavailable: ${err instanceof Error ? err.message : err}`,
    )
    return []
  }
}

/** Put a delivered post on the re-check list and remember its state. */
async function rememberSent(rec: RelayRecord): Promise<void> {
  const id = rec.id
  await redis.zAdd(SENT_ZSET, {member: id, score: rec.created})
  await redis.set(stageKey(id), '0', {expiration: ttl()})
  await redis.set(
    stateKey(id),
    stateKeyOf({
      removed: rec.removed,
      deleted: false,
      edited: !!rec.edited,
      spoiler: rec.spoiler,
      nsfw: rec.nsfw,
      locked: false,
    }),
    {expiration: ttl()},
  )
  await redis.set(bodyHashKey(id), bodyHash(rec.body), {expiration: ttl()})
}

/**
 * Look again at recently delivered posts (~5 min, 30 min, 2 h, 6 h and 24 h
 * after creation) and tell the readers what Reddit shows now: one batched
 * `v: 2` update message per poll (first look always, later looks on change),
 * and a re-sent `v: 1` record (`revision` ≥ 2, `resent` = why) when the body
 * was edited, when a removed/filtered post became live again (approval), or
 * when an official post's author commented (0.0.8: `opComments` in
 * record.json). Readers keep the newest message per id, so a re-sent record
 * simply supersedes.
 */
async function recheckDelivered(
  webhook: string,
  enabled: boolean,
  startedAt: number,
  result: PollResult,
  officialUsers: string[],
): Promise<void> {
  const now = Math.floor(Date.now() / 1000)
  await redis.zRemRangeByScore(SENT_ZSET, 0, now - RECHECK_WINDOW_SECONDS - 1)
  const rows = await redis.zRange(
    SENT_ZSET,
    now - RECHECK_WINDOW_SECONDS,
    now,
    {by: 'score'},
  )
  type Due = {id: string; created: number; stage: number}
  const due: Due[] = []
  for (const {member, score} of rows) {
    const stage = dueStage(now - score)
    if (stage === 0) continue
    const done = Number((await redis.get(stageKey(member))) ?? '0')
    if (stage > done) due.push({id: member, created: score, stage})
  }
  // Oldest first: the last stage of an old post before the first of a new one
  // would starve nothing — the list is short — but keeps the order stable.
  due.sort((a, b) => a.created - b.created)

  const items: UpdateItem[] = []
  for (const d of due.slice(0, MAX_RECHECKS_PER_POLL)) {
    if (Date.now() - startedAt > POLL_SOFT_DEADLINE_MS) break
    let post: Awaited<ReturnType<typeof reddit.getPostById>>
    try {
      post = await reddit.getPostById(`t3_${d.id}`)
    } catch (err) {
      // A deleted post can 404 here; report it as deleted rather than silent.
      const msg = err instanceof Error ? err.message : String(err)
      if (/404|not found/i.test(msg)) {
        items.push({
          id: d.id,
          sub: '',
          age: now - d.created,
          stage: d.stage,
          removed: 'deleted',
          deleted: true,
          edited: false,
          spoiler: false,
          nsfw: false,
          locked: false,
          score: 0,
          comments: 0,
        })
        await redis.set(stageKey(d.id), `${d.stage}`, {expiration: ttl()})
        result.rechecked++
      } else {
        result.errors.push(describe(`recheck ${d.id}`, err))
      }
      continue
    }
    result.rechecked++
    const item: UpdateItem = {
      id: d.id,
      sub: post.subredditName,
      age: now - d.created,
      stage: d.stage,
      removed: post.removedByCategory ?? null,
      deleted:
        post.authorName === '[deleted]' || post.removedByCategory === 'deleted',
      edited: !!post.edited,
      spoiler: !!post.spoiler,
      nsfw: !!post.nsfw,
      locked: !!post.locked,
      score: post.score ?? 0,
      comments: post.numberOfComments ?? 0,
    }
    const previous = (await redis.get(stateKey(d.id))) ?? null
    if (shouldReport(item, previous)) items.push(item)
    await redis.set(stateKey(d.id), stateKeyOf(item), {expiration: ttl()})
    await redis.set(stageKey(d.id), `${d.stage}`, {expiration: ttl()})

    // Re-send the complete record when the readers need it again:
    //  • edited body (hash changed),
    //  • approved — removed/filtered/deleted before, live now (the readers'
    //    6 h window may have lost the original record by then),
    //  • the publisher's own comments changed (official posts only; the
    //    readers merge them into the post text / card).
    if (!item.deleted && !item.removed && enabled) {
      const reasons: string[] = []
      const hash = bodyHash(post.body ?? '')
      if (item.edited && (await redis.get(bodyHashKey(d.id))) !== hash)
        reasons.push('edited')
      if (becameLive(previous, item)) reasons.push('approved')
      let opComments: OpComment[] | null = null
      let ocHash = ''
      const rec = toRecord(post, post.subredditName)
      if (isOfficialRecord(rec, officialUsers)) {
        opComments = await authorComments(post)
        ocHash = opCommentsHash(opComments)
        if (opComments.length > 0 && (await redis.get(`oc:${d.id}`)) !== ocHash)
          reasons.push('comments')
      }
      if (reasons.length > 0) {
        rec.revision =
          (Number((await redis.get(`rev:${d.id}`)) ?? '1') || 1) + 1
        rec.resent = reasons.join('+')
        if (opComments && opComments.length > 0)
          rec.opCommentCount = opComments.length
        const full = await completeRecord(rec, result)
        if (opComments && opComments.length > 0) full.opComments = opComments
        if ((await deliver(webhook, rec, full)) === 'ok') {
          await redis.set(bodyHashKey(d.id), hash, {expiration: ttl()})
          if (ocHash) await redis.set(`oc:${d.id}`, ocHash, {expiration: ttl()})
          await redis.set(`rev:${d.id}`, `${rec.revision}`, {
            expiration: ttl(),
          })
          result.resent++
        }
      }
    }
  }

  if (items.length === 0 || !enabled) return
  for (const content of toUpdateContents(items, now)) {
    const outcome = await deliverContent(
      webhook,
      toWebhookBody(content),
      'update',
    )
    if (outcome === 'ok') result.updates++
    else result.errors.push(`update batch: Discord ${outcome}`)
  }
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
    distinguishedBy?: string | undefined
    spoiler: boolean
    nsfw: boolean
    score: number
    numberOfComments: number
    removedByCategory?: string | undefined
    crosspostParentId?: string | undefined
    body?: string | undefined
    edited?: boolean | undefined
    gallery: {url: string}[]
    secureMedia?:
      | {
          redditVideo?: {
            fallbackUrl?: string
            hlsUrl?: string
            isGif?: boolean
          }
        }
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
    distinguished: p.distinguishedBy ?? null,
    spoiler: !!p.spoiler,
    nsfw: !!p.nsfw,
    score: p.score ?? 0,
    comments: p.numberOfComments ?? 0,
    removed: p.removedByCategory ?? null,
    xpost: p.crosspostParentId ?? null,
    media,
    body: p.body ?? '',
    bodyTruncated: false,
    full: true,
    edited: !!p.edited,
    xpostPermalink: null,
    video: video
      ? {
          fallback: video.fallbackUrl,
          hls: video.hlsUrl,
          gif: !!video.isGif,
        }
      : null,
  }
}

// ---------------------------------------------------------------------------
// Discord
// ---------------------------------------------------------------------------

/**
 * Send one record. 0.0.7: the message carries the trimmed fenced record as
 * content (what every reader parses) AND the complete record as the
 * `record.json` attachment. If the multipart form is refused (4xx), the same
 * record goes out as plain JSON content exactly as before 0.0.7, so a post
 * can never be lost to the attachment; three refusals in a row pause the
 * attachment for an hour.
 */
async function deliver(
  webhook: string,
  rec: RelayRecord,
  full: FullRecord | null = null,
): Promise<'ok' | 'retry' | 'drop'> {
  const content = toContent(rec)
  if (full && !(await redis.get('attach:off'))) {
    const {body, contentType} = toMultipartBody(content, full)
    const outcome = await deliverContent(webhook, body, rec.id, contentType)
    if (outcome !== 'drop') {
      if (outcome === 'ok') await redis.del('attach:fails')
      return outcome
    }
    const fails = await redis.incrBy('attach:fails', 1)
    console.error(
      `[${rec.id}] attachment refused (${fails}x) — sending content only`,
    )
    if (fails >= ATTACH_FAILS_BEFORE_PAUSE) {
      await redis.set('attach:off', '1', {
        expiration: new Date(Date.now() + ATTACH_PAUSE_SECONDS * 1000),
      })
      await redis.del('attach:fails')
    }
  }
  const plain = toContent({...rec, full: false})
  return deliverContent(webhook, toWebhookBody(plain), rec.id)
}

async function deliverContent(
  webhook: string,
  body: string,
  label: string,
  contentType = 'application/json',
): Promise<'ok' | 'retry' | 'drop'> {
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const rsp = await fetch(`${webhook}?wait=true`, {
        method: 'POST',
        headers: {'Content-Type': contentType},
        body,
        signal: AbortSignal.timeout(DISCORD_TIMEOUT_MS),
      })
      const outcome = classifyStatus(rsp.status)
      if (outcome === 'ok') return 'ok'
      if (outcome === 'drop') {
        console.error(
          `[${label}] Discord HTTP ${rsp.status}: ${(await rsp.text()).slice(0, 200)}`,
        )
        return 'drop'
      }
      if (rsp.status === 429 && attempt === 0) {
        const retryAfter = Number(rsp.headers.get('retry-after') ?? '1')
        await sleep(Math.min(Math.max(retryAfter, 0.5), 5) * 1000)
        continue
      }
      console.error(
        `[${label}] Discord HTTP ${rsp.status} — will retry next poll`,
      )
      return 'retry'
    } catch (err) {
      console.error(
        `[${label}] Discord request error: ${err instanceof Error ? err.message : err}`,
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
  const base = `poll: ${r.subs} subs, ${r.users} users, ${r.fetched} fetched, ${r.sent} sent, ${r.skipped} seen, ${r.failed} failed, ${r.bootstrapped} bootstrapped; recheck ${r.rechecked} looked, ${r.updates} update msg, ${r.resent} re-sent`
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
