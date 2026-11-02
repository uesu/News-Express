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
  /** "moderator" | "admin" when the post is distinguished, else null (0.0.4 code).
   *  Classification stays with the consumer: for a publisher without a u/
   *  account (Wuthering Waves) the signal is `flair` ("Official News" on
   *  r/WutheringWaves, community-posted); this field adds mod/admin notices. */
  distinguished: string | null
  spoiler: boolean
  nsfw: boolean
  score: number
  comments: number
  removed: string | null // removedByCategory, null when live
  xpost: string | null // crosspostParentId (t3_…) or null
  media: string[] // image / video URLs, oldest-first gallery order
  body: string // selftext markdown, possibly truncated
  bodyTruncated: boolean
  // ---- 0.0.7 additions (all optional; v1 readers ignore unknown keys) ----
  /** true when the message also carries `record.json` — the complete record
   *  (untruncated body, every media URL, video renditions, crosspost parent). */
  full?: boolean
  /** true when `media` lost entries to the message budget (the attachment has all). */
  mediaTruncated?: boolean
  /** Reddit's `edited` flag at relay time; a re-sent record after an edit
   *  carries `revision` ≥ 2 (readers keep the newest message per id). */
  edited?: boolean
  revision?: number
  /** Crosspost parent permalink (`/r/<sub>/comments/<id>/…/`) when known. */
  xpostPermalink?: string | null
  /** Reddit-hosted video renditions, when the post is a v.redd.it video. */
  video?: {fallback?: string; hls?: string; gif?: boolean} | null
}

/** The complete record: the same shape as RelayRecord but never trimmed, plus
 *  the crosspost parent as a nested record. Shipped as the `record.json`
 *  attachment of the same Discord message. */
export type FullRecord = RelayRecord & {
  parent?: RelayRecord | null
}

/** One post's live state as re-checked by the relay after delivery (0.0.7). */
export type UpdateItem = {
  id: string
  sub: string
  /** seconds since creation at check time */
  age: number
  /** re-check stage that produced this item (1 = first look, ~10 min) */
  stage: number
  removed: string | null // removedByCategory, null when live
  deleted: boolean // author account or post deleted
  edited: boolean
  spoiler: boolean
  nsfw: boolean
  locked: boolean
  score: number
  comments: number
}

/** A batched liveness update message. `v: 2` on purpose: pre-0.0.7 readers
 *  accept `v: 1` only and therefore ignore these messages entirely. */
export type UpdateMessage = {
  v: 2
  kind: 'update'
  at: number // unix seconds
  posts: UpdateItem[]
}

/** Re-check schedule after delivery: the stage a post of `ageSeconds` is due
 *  for (0 = not yet). Four looks per post: ~10 min (modqueue / AutoMod
 *  removals surface here), 30 min, 2 h, 6 h. */
export const RECHECK_STAGES_SECONDS = [600, 1800, 7200, 21600] as const

export function dueStage(ageSeconds: number): number {
  let stage = 0
  for (const [i, at] of RECHECK_STAGES_SECONDS.entries())
    if (ageSeconds >= at) stage = i + 1
  return stage
}

/** The fields whose change is worth a message. Score/comment counts are
 *  carried but never trigger one. */
const STATE_FIELDS = [
  'removed',
  'deleted',
  'edited',
  'spoiler',
  'nsfw',
  'locked',
] as const

/** Compact state string stored in Redis (`state:<id>`) and compared between
 *  looks. */
export function stateKeyOf(
  item: Pick<UpdateItem, (typeof STATE_FIELDS)[number]>,
): string {
  return STATE_FIELDS.map(f => `${f}=${String(item[f])}`).join('|')
}

/** Whether an item must be sent: the first look is always reported (it is the
 *  readers' positive "still listed" verdict), later looks only on change. */
export function shouldReport(
  item: UpdateItem,
  previousState: string | null,
): boolean {
  if (item.stage <= 1) return true
  return previousState !== stateKeyOf(item)
}

/** Serialise update items into as few fenced messages as fit the budget. */
export function toUpdateContents(
  items: UpdateItem[],
  at: number,
  budget = CONTENT_BUDGET,
): string[] {
  const wrap = (posts: UpdateItem[]): string =>
    `\`\`\`json\n${JSON.stringify({v: 2, kind: 'update', at, posts} satisfies UpdateMessage)}\n\`\`\``
  const out: string[] = []
  let batch: UpdateItem[] = []
  for (const item of items) {
    const next = [...batch, item]
    if (batch.length > 0 && wrap(next).length > budget) {
      out.push(wrap(batch))
      batch = [item]
    } else {
      batch = next
    }
  }
  if (batch.length > 0) out.push(wrap(batch))
  return out
}

/** Redis keys for the post-delivery re-check (0.0.7). */
export const SENT_ZSET = 'sent:z'
export function stageKey(id: string): string {
  return `stage:${bareId(id)}`
}
export function stateKey(id: string): string {
  return `state:${bareId(id)}`
}
export function bodyHashKey(id: string): string {
  return `bh:${bareId(id)}`
}

/** Cheap stable hash (FNV-1a, 32 bit) of a body — enough to notice an edit. */
export function bodyHash(s: string): string {
  let h = 0x811c9dc5
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 0x01000193) >>> 0
  }
  return h.toString(16).padStart(8, '0')
}

/** Multipart webhook body: the fenced content as `payload_json` plus the
 *  complete record as the `record.json` file. Built by hand as one string so
 *  it needs nothing beyond `fetch(url, {body: string})`. */
export function toMultipartBody(
  content: string,
  full: FullRecord,
  filename = 'record.json',
): {body: string; contentType: string} {
  const fileText = JSON.stringify(full)
  const payload = JSON.stringify({
    content,
    allowed_mentions: {parse: []},
    attachments: [
      {id: 0, filename, description: `relay record ${full.id} (complete)`},
    ],
  })
  let boundary = `----GamingExpress${Date.now().toString(36)}`
  let n = 0
  while (fileText.includes(boundary) || payload.includes(boundary))
    boundary = `----GamingExpress${Date.now().toString(36)}x${++n}`
  const body =
    `--${boundary}\r\n` +
    `Content-Disposition: form-data; name="payload_json"\r\n` +
    `Content-Type: application/json\r\n\r\n${payload}\r\n` +
    `--${boundary}\r\n` +
    `Content-Disposition: form-data; name="files[0]"; filename="${filename}"\r\n` +
    `Content-Type: application/json\r\n\r\n${fileText}\r\n` +
    `--${boundary}--\r\n`
  return {body, contentType: `multipart/form-data; boundary=${boundary}`}
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

  // 2. shrink the media list (the complete list travels in record.json)
  while (r.media.length > 0 && text.length > budget) {
    r = {...r, media: r.media.slice(0, -1), mediaTruncated: true}
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
