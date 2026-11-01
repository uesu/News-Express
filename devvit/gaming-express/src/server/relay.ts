/**
 * Pure relay logic — no Devvit imports, so it is unit-testable with the plain
 * Node test runner (`npm run test:unit`). server.ts wires it to Devvit.
 */

/** The subset of a Reddit post the relay forwards. Field names are stable:
 *  the consumer (News-Express intake reader) keys on them. */
export type RelayRecord = {
  v: 1
  id: string
  sub: string
  title: string
  permalink: string
  url: string
  created: number // unix seconds
  author: string
  flair: string | null
  spoiler: boolean
  nsfw: boolean
  score: number
  comments: number
  removed: string | null // removedByCategory, null when live
  xpost: string | null // crosspostParentId (t3_…) or null
  media: string[] // image / video URLs, oldest-first gallery order
  body: string // selftext markdown, possibly truncated
  bodyTruncated: boolean
}

/** Discord message content hard limit is 2000; keep a margin for the fence. */
export const CONTENT_BUDGET = 1900

function parseNames(raw: string | undefined | null, prefix: RegExp): string[] {
  const out: string[] = []
  for (const part of (raw ?? '').split(',')) {
    const name = part.trim().replace(prefix, '')
    if (!name) continue
    if (!/^[A-Za-z0-9_-]{2,50}$/.test(name)) continue
    if (!out.some(x => x.toLowerCase() === name.toLowerCase())) out.push(name)
  }
  return out
}

/** `subreddits` setting → unique subreddit names (accepts `r/Name`, `/r/Name`, `Name`). */
export function parseSubreddits(raw: string | undefined | null): string[] {
  return parseNames(raw, /^\/?r\//i)
}

/** `officialUsers` setting → unique account names (accepts `u/Name`, `/u/Name`, `Name`). */
export function parseUsers(raw: string | undefined | null): string[] {
  return parseNames(raw, /^\/?u(?:ser)?\//i)
}

/**
 * `relayEnabled` as actually stored. The CLI (`npx devvit settings set relayEnabled`)
 * writes the typed text, so a paused relay may arrive as the string `"false"` rather
 * than the boolean `false`; v0.0.2 compared `!== false` and kept sending (observed
 * 2026-11-01 14:39–15:11 PHT). Anything unset or unrecognised means enabled.
 */
export function parseEnabled(raw: unknown): boolean {
  if (raw === false) return false
  if (typeof raw === 'string') {
    const v = raw.trim().toLowerCase()
    if (
      v === 'false' ||
      v === '0' ||
      v === 'no' ||
      v === 'off' ||
      v === 'paused'
    )
      return false
  }
  return true
}

/** Drop records whose id already appeared earlier in the list (an official account's
 *  post shows up both in its `u/` feed and in the subreddit listing). Keeps the first. */
export function uniqueById<T extends {id: string}>(xs: T[]): T[] {
  const seen = new Set<string>()
  const out: T[] = []
  for (const x of xs) {
    const k = bareId(x.id).toLowerCase()
    if (seen.has(k)) continue
    seen.add(k)
    out.push(x)
  }
  return out
}

/**
 * Bare post id: Reddit's listing returns `t3_1xkvvda`, the relayed record
 * carries `1xkvvda`. Every Redis key must be built from the same form,
 * otherwise a post sent under one spelling is never recognised under the
 * other and is re-sent on every poll (the 2026-11-01 first-run defect).
 */
export function bareId(id: string): string {
  return id.replace(/^t3_/i, '')
}

/** Redis key for the per-post de-dup marker (always the bare id). */
export function seenKey(id: string): string {
  return `seen:${bareId(id)}`
}

/**
 * Key spelling used by v0.0.1 for bootstrap markers (`seen:t3_<id>`). Read
 * alongside `seenKey` so an upgrade never re-sends posts that were already
 * remembered under the old spelling; expires naturally with its 7-day TTL.
 */
export function legacySeenKey(id: string): string {
  return `seen:t3_${bareId(id)}`
}

/** Redis key marking that a target's first poll already ran (bootstrap).
 *  Subreddits keep the v0.0.1 spelling (`boot:<sub>`); user feeds use `boot:u/<name>`. */
export function bootKey(target: string): string {
  return `boot:${target.toLowerCase()}`
}

/** Bootstrap-key label for an official account feed. */
export function userTarget(user: string): string {
  return `u/${user}`
}

/** Redis key counting delivery failures for a post (always the bare id). */
export function failKey(id: string): string {
  return `fail:${bareId(id)}`
}

/**
 * Serialise a record into Discord message content that fits the budget.
 * Trims the body first, then the media list, never the identity fields.
 * The content is a single fenced JSON block so humans can read it in the
 * channel and machines can `JSON.parse` the inside of the fence.
 */
export function toContent(rec: RelayRecord, budget = CONTENT_BUDGET): string {
  const wrap = (r: RelayRecord): string =>
    `\`\`\`json\n${JSON.stringify(r)}\n\`\`\``
  let r: RelayRecord = {...rec}
  let text = wrap(r)
  if (text.length <= budget) return text

  // 1. shrink the body
  const overhead = wrap({...r, body: ''}).length
  const room = Math.max(0, budget - overhead - 1)
  if (r.body.length > room) {
    r = {...r, body: truncate(r.body, room), bodyTruncated: true}
    text = wrap(r)
    if (text.length <= budget) return text
  }

  // 2. shrink the media list
  while (r.media.length > 0 && text.length > budget) {
    r = {...r, media: r.media.slice(0, -1)}
    text = wrap(r)
  }
  if (text.length <= budget) return text

  // 3. last resort: drop the body entirely
  r = {...r, body: '', bodyTruncated: true}
  return wrap(r)
}

/** Cut on a character boundary and mark the cut. JSON escaping can expand
 *  characters, so leave a little slack for that. */
function truncate(s: string, max: number): string {
  if (max <= 1) return ''
  const slack = Math.floor(max * 0.1)
  const cut = Math.max(0, max - slack - 1)
  return `${s.slice(0, cut)}…`
}

/** Discord webhook body. Mentions are disabled so a post title can never
 *  ping a role or @everyone in the intake channel. */
export function toWebhookBody(content: string): string {
  return JSON.stringify({content, allowed_mentions: {parse: []}})
}

/** Only accept Discord webhook URLs — never relay to an arbitrary host. */
export function isDiscordWebhook(url: string | undefined | null): boolean {
  if (!url) return false
  try {
    const u = new URL(url)
    return (
      u.protocol === 'https:' &&
      u.hostname === 'discord.com' &&
      /^\/api\/webhooks\/\d+\/[A-Za-z0-9_-]+\/?$/.test(u.pathname)
    )
  } catch {
    return false
  }
}

/** Classify a Discord response for the retry policy. */
export type DeliveryOutcome = 'ok' | 'retry' | 'drop'

export function classifyStatus(status: number): DeliveryOutcome {
  if (status === 200 || status === 204) return 'ok'
  if (status === 429 || status >= 500) return 'retry'
  return 'drop' // 400/401/403/404: the webhook is gone or the payload is bad
}

/** Oldest first so the channel order matches Reddit's chronology. */
export function sortOldestFirst<T extends {created: number}>(xs: T[]): T[] {
  return [...xs].sort((a, b) => a.created - b.created)
}
