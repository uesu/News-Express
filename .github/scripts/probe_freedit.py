#!/usr/bin/env python3
"""Manual, public-endpoint diagnostic. No monitor imports, credentials or posting.

Only fixed URLs below may be fetched. Each endpoint runs in a child process to
bound DNS/connect/read time as a whole. No retries, WAF bypass, token forwarding,
cookies or proxy environment. Remote bodies are parsed, never executed or saved.
A successful probe is an observation, not a guarantee about all datacenter IPs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import xml.etree.ElementTree as ET

MAX_BYTES = 2 * 1024 * 1024
SOCKET_TIMEOUT = 12
ENDPOINT_DEADLINE = 20
PAUSE_SECONDS = 2
SUB = "Genshin_Impact_Leaks"
ACCOUNT = "TYPEII_EN"
REDDIT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
# These include the user's URLs AND the different RSS path used by the engine.
# Controls are observations too: they may fail or change between requests.
ENDPOINTS = {
    "redlib_home": ("https://redlib.freedit.eu/", "home", False),
    "redlib_requested_rss": (f"https://redlib.freedit.eu/r/{SUB}/new.rss?limit=100", "reddit_feed", False),
    "redlib_engine_rss": (f"https://redlib.freedit.eu/r/{SUB}/new/.rss", "reddit_feed", False),
    "redlib_requested_html": (f"https://redlib.freedit.eu/r/{SUB}/new?limit=100", "listing", False),
    "redlib_pristine_html": (f"https://redlib.freedit.eu/r/{SUB}/new?limit=100", "listing", True),
    "nitter_requested_rss": (f"https://nitter.freedit.eu/{ACCOUNT}/rss", "twitter_feed", False),
    "nitter_control_rss": (f"https://nitter.cf/{ACCOUNT}/rss", "twitter_feed", False),
    "redlib_control_html": (f"https://redlib.catsarch.com/r/{SUB}/new?limit=100", "listing", True),
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def request_details(name, fresh_ms=None):
    url, kind, pristine = ENDPOINTS[name]
    headers = {"User-Agent": "Mozilla/5.0" if kind == "twitter_feed" else REDDIT_UA,
               "Accept-Encoding": "identity"}
    if kind == "reddit_feed":
        headers["Accept"] = "application/rss+xml, application/xml, text/xml, */*"
    elif kind != "twitter_feed":
        headers["Accept"] = "*/*"
    if pristine:
        url += f"&_fresh={int(time.time() * 1000) if fresh_ms is None else fresh_ms}"
        headers.update({"Cache-Control": "no-cache, no-store", "Pragma": "no-cache"})
    return url, headers


class SameHostRedirects(HTTPRedirectHandler):
    """Do not silently test a different provider or follow an HTTPS downgrade."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        original, target = urlsplit(req.full_url), urlsplit(newurl)
        if (target.scheme != "https" or target.hostname != original.hostname
                or target.username or target.password or target.port not in (None, 443)):
            raise HTTPError(req.full_url, code, "redirect outside tested origin", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def local_tag(tag):
    return tag.rsplit("}", 1)[-1].lower()


def entry_date(entry):
    for child in entry:
        if local_tag(child.tag) not in ("pubdate", "published", "updated", "date"):
            continue
        text = (child.text or "").strip()
        try:
            value = parsedate_to_datetime(text)
        except (TypeError, ValueError, OverflowError):
            try:
                value = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError:
                continue
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).isoformat()
    return None


def matching_id(link, kind):
    path = urlsplit(link).path
    if kind == "twitter_feed":
        match = re.match(rf"^/{ACCOUNT}/status/(\d+)(?:/|$)", path, re.I)
    else:
        match = re.match(rf"^/r/{SUB}/comments/([a-z0-9]+)(?:/|$)", path, re.I)
    return match.group(1).lower() if match else None


class ListingLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href") or ""
            try:
                post_id = matching_id(href, "reddit_feed")
            except ValueError:
                return
            if post_id:
                self.ids.add(post_id)


class NoDTDTreeBuilder(ET.TreeBuilder):
    def doctype(self, name, pubid, system):
        # Parser-level rejection also covers UTF-16/32 declarations, which a
        # decoded-text precheck alone could miss.
        raise ValueError("DTD not allowed in diagnostic feed")


def inspect_body(body, kind):
    text = body.decode("utf-8", errors="replace")
    lower = text.lower()
    markers = [name for name, needle in (
        ("reddit_error", "reddit error"), ("bad_request", "bad request"),
        ("rss_disabled", "rss feed is disabled"), ("anubis", "anubis"),
        ("goaway_challenge", "__goaway"), ("gandalf_challenge", "__gandalf"),
        ("cloudflare_challenge", "cf-chl-"), ("javascript_required", "enable javascript"),
    ) if needle in lower]
    result = {"markers": markers}
    if kind in ("twitter_feed", "reddit_feed"):
        # Reject DTDs/entities explicitly; diagnostics should not expand hostile XML.
        if "<!doctype" in lower or "<!entity" in lower:
            return {**result, "body_class": "non_feed_or_dtd", "matching_entries": 0}
        try:
            root = ET.fromstring(body, parser=ET.XMLParser(target=NoDTDTreeBuilder()))
        except (ET.ParseError, ValueError):
            return {**result, "body_class": "not_feed_xml", "matching_entries": 0}
        if local_tag(root.tag) not in ("rss", "feed", "rdf"):
            return {**result, "body_class": "non_feed_xml", "matching_entries": 0}
        entries = [e for e in root.iter() if local_tag(e.tag) in ("item", "entry")]
        records = []
        for entry in entries:
            for child in entry:
                if local_tag(child.tag) != "link" or child.get("rel", "alternate") != "alternate":
                    continue
                link = child.get("href") or (child.text or "").strip()
                try:
                    post_id = matching_id(link, kind)
                except ValueError:
                    continue
                if post_id:
                    records.append({"id": post_id, "date_utc": entry_date(entry)})
                    break
        records.sort(key=lambda r: r["date_utc"] or "", reverse=True)
        return {**result, "body_class": "feed_with_matching_entries" if records else "feed_without_matching_entries",
                "entries": len(entries), "matching_entries": len(records), "newest_matching": records[:5]}
    if kind == "listing":
        parser = ListingLinks()
        parser.feed(text)
        ages = [int(n) * {"second": 1, "minute": 60, "hour": 3600, "day": 86400}[unit.lower()]
                for n, unit in re.findall(r">\s*(\d+)\s+(second|minute|hour|day)s?\s+ago\s*<", text, re.I)]
        return {**result, "body_class": "listing_with_post_links" if parser.ids else "html_without_post_links",
                "post_ids_count": len(parser.ids), "post_ids_sample": sorted(parser.ids)[:10],
                "oldest_visible_age_seconds": max(ages) if ages else None}
    return {**result, "body_class": "homepage_only_not_feed_evidence"}


def fetch_endpoint(name):
    url, headers = request_details(name)
    _, kind, pristine = ENDPOINTS[name]
    result = {"endpoint": name, "requested_url": url, "started_utc": utc_now(),
              "pristine_request": pristine, "kind": kind}
    start = time.monotonic()
    # Explicitly disable ambient proxies and use no cookie or auth handlers.
    opener = build_opener(ProxyHandler({}), SameHostRedirects())
    try:
        try:
            response = opener.open(Request(url, headers=headers), timeout=SOCKET_TIMEOUT)
        except HTTPError as exc:
            response = exc  # Read the error body, bounded, to identify HTML/XML errors.
        with response as response:
            result.update({"http_status": response.code, "final_url": response.geturl(),
                           "content_type": response.headers.get("Content-Type", "")[:160],
                           "content_encoding": response.headers.get("Content-Encoding", "identity")[:40]})
            location = response.headers.get("Location")
            if location:
                # Never retain userinfo or query values from an untrusted redirect.
                dest = urlsplit(urljoin(url, location))
                result["redirect_to"] = f"{dest.scheme}://{dest.hostname or ''}{dest.path}"[:300]
            for header in ("Age", "Cache-Control", "CF-Cache-Status", "Retry-After"):
                if response.headers.get(header):
                    result[header.lower()] = response.headers[header][:160]
            body = response.read(MAX_BYTES + 1)
            result["bytes_read"] = len(body)
            if len(body) > MAX_BYTES:
                result["body_class"] = "oversize_not_parsed"
            else:
                result.update(inspect_body(body, kind))
            # Do not equate valid-looking body text on an error page with success.
            result["candidate_response"] = bool(
                response.code == 200 and result.get("body_class") in
                ("feed_with_matching_entries", "listing_with_post_links")
                and (kind != "listing" or "html" in result["content_type"].lower())
                and not result.get("markers"))
    except (URLError, OSError, ValueError) as exc:
        result.update({"transport_error": type(exc).__name__,
                       "transport_reason_class": type(getattr(exc, "reason", exc)).__name__,
                       "candidate_response": False})
    result["elapsed_seconds"] = round(time.monotonic() - start, 3)
    return result


def probe_bounded(name):
    try:
        run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--endpoint", name],
                             capture_output=True, text=True, timeout=ENDPOINT_DEADLINE, check=False)
    except subprocess.TimeoutExpired:
        return {"endpoint": name, "body_class": "total_deadline_exceeded", "candidate_response": False}
    if run.returncode:
        return {"endpoint": name, "body_class": "probe_worker_failed", "candidate_response": False}
    try:
        return json.loads(run.stdout)
    except json.JSONDecodeError:
        return {"endpoint": name, "body_class": "invalid_worker_output", "candidate_response": False}


def summary(report):
    lines = ["## Freedit public-endpoint probe", "",
             "**Diagnostic only:** no tokens, Discord calls, monitor runs or cache writes.",
             "A success proves one request, not a permanent no-datacenter-block policy.", "",
             "| Endpoint | HTTP | Body classification | Matching items | Candidate |",
             "|---|---:|---|---:|---|"]
    for row in report["results"]:
        # All fields below are generated locally from fixed keys, ints and enum strings.
        lines.append(f'| {row["endpoint"]} | {row.get("http_status", "—")} | '
                     f'{row.get("body_class", row.get("transport_error", "unknown"))} | '
                     f'{row.get("matching_entries", row.get("post_ids_count", "—"))} | '
                     f'{"yes" if row.get("candidate_response") else "no"} |')
    lines += ["", "Candidate = HTTP 200 with matching post links/feed entries and no detected error marker (listings also require HTML Content-Type).",
              "It is NOT a freshness certificate or automatic production approval.",
              "See the JSON in the step log for dates, sampled IDs, redirects and cache headers.",
              "Compare the control results; do not classify a quiet account as stale merely by age.",
              "All endpoints are reported even when some fail. A green job means the diagnostic completed."]
    return "\n".join(lines) + "\n"


def annotation_commands(report):
    """Expose bounded public results via Checks API, without a write token.

    Escape workflow-command metacharacters even in JSON, since a public server
    controls headers/redirects. No remote body or credentials are included.
    """
    records = [{k: v for k, v in report.items() if k != "results"}, *report["results"]]
    for record in records:
        data = json.dumps(record, ensure_ascii=True, separators=(",", ":"))
        data = data.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        yield "::notice title=Freedit diagnostic result::" + data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", choices=list(ENDPOINTS), help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path, default=Path("freedit-probe-results.json"))
    parser.add_argument("--annotations", action="store_true", help="Emit escaped GitHub check notices")
    args = parser.parse_args()
    if args.endpoint:
        print(json.dumps(fetch_endpoint(args.endpoint), ensure_ascii=True))
        return
    report = {"generated_utc": utc_now(), "github_actions": os.getenv("GITHUB_ACTIONS") == "true",
              "runner_os": os.getenv("RUNNER_OS", "unknown"),
              "runner_arch": os.getenv("RUNNER_ARCH", "unknown"),
              "runner_environment": os.getenv("RUNNER_ENVIRONMENT", "unknown"),
              "run_id": os.getenv("GITHUB_RUN_ID", ""),
              "note": "Read region/cloud from Set up job logs; the runner label does not prove Azure region.",
              "results": []}
    for i, name in enumerate(ENDPOINTS):
        if i:
            time.sleep(PAUSE_SECONDS)
        report["results"].append(probe_bounded(name))
    data = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    args.output.write_text(data, encoding="utf-8")
    print(data, end="")
    if args.annotations:
        for command in annotation_commands(report):
            print(command)
    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as stream:
            stream.write(summary(report))


if __name__ == "__main__":
    main()
