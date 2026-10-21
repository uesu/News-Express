#!/usr/bin/env python3
"""
Render Reddit monitor run summary from stable local reddit_run_result.json.
No network calls, no scraping of prose logs. Writes to GITHUB_STEP_SUMMARY.
"""
import json
import os
import pathlib
import sys

def main():
    runtime = os.environ.get("RUNTIME", "unavailable")
    cache_result = os.environ.get("CACHE_RESULT", "unavailable")
    job_status = os.environ.get("JOB_STATUS", "unavailable")

    # Also support fallback env names
    if runtime == "unavailable":
        runtime = os.environ.get("runtime", runtime)
    if cache_result == "unavailable":
        cache_result = os.environ.get("CACHE_RESULT_ENV", cache_result)

    run_result_path = pathlib.Path("reddit_run_result.json")
    data = {}
    if run_result_path.exists():
        try:
            data = json.loads(run_result_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    def v(key, default="unavailable"):
        val = data.get(key)
        return str(val) if val is not None else default

    def dict_str(d):
        if not isinstance(d, dict) or not d:
            return "none"
        return ", ".join(f"{k}: {v}" for k, v in sorted(d.items()))

    out = os.environ.get("GITHUB_STEP_SUMMARY")
    if not out:
        # For local testing, print to stdout
        out_path = None
    else:
        out_path = pathlib.Path(out)

    lines = []
    lines.append("## Reddit Feed Monitor — run summary")
    lines.append("")
    lines.append(f"**Result:** {job_status}")
    lines.append(f"**Monitor runtime:** {runtime}")
    lines.append(f"**State persistence:** {cache_result}")
    lines.append("")
    lines.append("### Feed")
    lines.append(f"- Combined-feed entries: {v('combined_entries')}")
    lines.append(f"- Subreddits represented: {v('subreddits_represented')} of {v('subreddits_configured')} configured")
    lines.append(f"- Unposted candidates considered: {v('unposted_candidates_considered')}")
    lines.append(f"- Candidates entering card processing: {v('candidates_entering_processing')}")
    lines.append(f"- Delivered posts: {v('delivered')}")
    if 'dry_run_would_deliver' in data:
        lines.append(f"- Dry-run would-deliver: {v('dry_run_would_deliver')}")
    lines.append(f"- Failed deliveries: {v('failed_delivery')}")
    lines.append("")
    lines.append("### Skipped and deferred")
    lines.append(f"- Known-rejected archive candidates: {v('known_pending_suppressed')}")
    if data.get('known_pending_by_reason'):
        lines.append(f"  - by reason: {dict_str(data.get('known_pending_by_reason'))}")
    lines.append(f"- Retry backoff: {v('retry_backoff')}")
    if data.get('retry_backoff_by_reason'):
        lines.append(f"  - by reason: {dict_str(data.get('retry_backoff_by_reason'))}")
    lines.append(f"- Fresh-age hold: {v('fresh_hold')}")
    lines.append(f"- Newly rejected removed/deleted: {v('newly_rejected_removed')}")
    if data.get('newly_rejected_by_reason'):
        lines.append(f"  - by reason: {dict_str(data.get('newly_rejected_by_reason'))}")
    lines.append(f"- Liveness not verified: {v('liveness_not_verified')}")
    if data.get('liveness_by_reason'):
        lines.append(f"  - by reason: {dict_str(data.get('liveness_by_reason'))}")
    lines.append(f"- Media-wait: {v('media_wait')}")
    lines.append(f"- Partial-gallery: {v('partial_gallery')}")
    lines.append(f"- Flood-cap dropped: {v('flood_cap_dropped')}")
    lines.append(f"- Dedup skipped in run: {v('dedup_skipped_in_run')}")
    lines.append(f"- Other skipped: {v('other_skipped')}")
    if data.get('other_by_reason'):
        lines.append(f"  - by reason: {dict_str(data.get('other_by_reason'))}")
    lines.append("")
    lines.append("### Providers and media")
    if 'combined_fetch_status' in data:
        lines.append(f"- Combined fetch status: {v('combined_fetch_status')}")
    lines.append("- Warmup results: see monitor.log (proxy warm-up)")
    lines.append("- Observed provider failures: see monitor.log; counts describe this run's local observations, not an independent health audit")
    lines.append("")
    lines.append("Counts describe this run's local observations, not an independent subreddit-visibility or end-to-end health audit.")
    lines.append("Summary source: reddit_run_result.json (stable local record) + monitor.log for provider diagnostics; no additional network requests.")
    lines.append("")

    output = "\n".join(lines) + "\n"
    if out_path:
        try:
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(output)
        except Exception as e:
            print(f"Failed to write summary: {e}", file=sys.stderr)
            print(output)
    else:
        print(output)

if __name__ == "__main__":
    main()
