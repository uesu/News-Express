#!/usr/bin/env python3
"""Shared, mostly-pure maintenance policy for News-Express and Game-Express.

Version selection, update classification, diff validation, check classification
and merge decisions live here so workflows stay thin. The merge controller
must read this file from the trusted default branch and must never execute
commands taken from a PR-head maintenance profile.

Decision mode is side-effect free: missing fixture fields fail closed and
never fall back to live GitHub writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import maintenance_common

SCHEMA_VERSION = 1
SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent.parent
DEFAULT_PROFILE = REPO_ROOT / ".github" / "maintenance.json"
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
PRERELEASE_RE = re.compile(r"(a|b|rc|dev|alpha|beta)", re.I)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USES_RE = re.compile(
    r"uses:\s*(?P<action>[^\s@#]+?)@(?P<ref>[0-9a-f]{40}|[^\s#]+)",
    re.I,
)
SECRET_ENV_HINTS = (
    "TOKEN", "SECRET", "WEBHOOK", "PASSWORD", "AUTHORIZATION", "COOKIE", "PAT",
)
HOLD_LABELS_FALLBACK = ("review-required", "do-not-merge", "hold", "changes-requested")
AUTO_YES = "yes"
DEFAULT_DEPENDABOT_ALLOWED = (
    "requirements.txt",
    "requirements.in",
    "requirements-dev.txt",
    "requirements-dev.in",
    ".github/dependabot.yml",
)
DEFAULT_DEPENDABOT_ACTIONS_ALLOWED = (
    ".github/workflows/ci.yml",
    ".github/workflows/maintenance_merge.yml",
    ".github/workflows/python_version_bump.yml",
    ".github/workflows/reddit_monitor.yml",
    ".github/workflows/twitter_monitor.yml",
)

# Highest-risk member of a grouped update controls the whole PR.
RISK_RANK = {
    "routine": 0,
    "security": 1,
    "review-required": 2,
    "blocked": 3,
}


@dataclass
class Version:
    major: int
    minor: int
    patch: int

    @property
    def tuple(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "Version") -> bool:
        return self.tuple < other.tuple

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Version) and self.tuple == other.tuple


@dataclass
class Candidate:
    version: Version
    kind: str  # patch | minor | major | none
    release_url: str = ""
    release_date: str | None = None
    source: str = "manifest"


@dataclass
class Decision:
    action: str
    reason: str
    risk: str = "blocked"
    merge_method: str | None = None
    candidate: str | None = None
    pr_url: str | None = None
    checks: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def load_profile(path: str | os.PathLike | None = None) -> dict[str, Any]:
    profile_path = Path(path) if path else DEFAULT_PROFILE
    with profile_path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not data:
        raise ValueError("maintenance profile is empty or not an object")
    return data


def parse_version(raw: str | None) -> Version:
    text = (raw or "").strip()
    match = VERSION_RE.fullmatch(text)
    if not match:
        raise ValueError(f"not a complete numeric X.Y.Z version: {raw!r}")
    return Version(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def read_pin(pin_file: str | os.PathLike | None = None) -> Version:
    path = Path(pin_file) if pin_file else REPO_ROOT / ".python-version"
    text = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    return parse_version(text)


def version_kind(current: Version, candidate: Version) -> str:
    if candidate.tuple == current.tuple:
        return "none"
    if candidate < current:
        return "downgrade"
    if candidate.major != current.major:
        return "major"
    if candidate.minor != current.minor:
        return "minor"
    return "patch"


def parse_iso_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = raw.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        value = datetime.fromisoformat(text)
    except ValueError:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _linux_x64(entry: Mapping[str, Any]) -> bool:
    files = entry.get("files") or []
    if not isinstance(files, list):
        return False
    for item in files:
        if not isinstance(item, dict):
            continue
        if item.get("platform") == "linux" and item.get("arch") == "x64":
            return True
    return False


def iter_stable_manifest_versions(manifest: Sequence[Mapping[str, Any]]) -> list[tuple[Version, dict[str, Any]]]:
    out: list[tuple[Version, dict[str, Any]]] = []
    for entry in manifest:
        if not isinstance(entry, dict) or not entry.get("stable"):
            continue
        raw = str(entry.get("version") or "")
        if PRERELEASE_RE.search(raw):
            continue
        try:
            version = parse_version(raw)
        except ValueError:
            continue
        if not _linux_x64(entry):
            continue
        out.append((version, entry))
    return out


def newest_in_series(versions: Iterable[tuple[Version, dict[str, Any]]], series: tuple[int, int]) -> tuple[Version, dict[str, Any]] | None:
    best: tuple[Version, dict[str, Any]] | None = None
    for version, entry in versions:
        if (version.major, version.minor) != series:
            continue
        if best is None or version > best[0]:
            best = (version, entry)
    return best


def select_python_candidate(
    current: Version,
    manifest: Sequence[Mapping[str, Any]],
    *,
    soak_days: int = 30,
    now: datetime | None = None,
    ignore_soak: bool = False,
    force: str | None = None,
    date_lookup=None,
) -> dict[str, Any]:
    """Return a structured selection result. Never proposes a major or a skip-minor leap.

    ``date_lookup(version, entry)`` may supply an ISO timestamp when the
    manifest omits ``release_date`` / ``published_at``. Fixture callers leave
    it unset so selection stays side-effect free.
    """
    now = now or datetime.now(timezone.utc)
    if force:
        try:
            forced = parse_version(force)
        except ValueError as exc:
            return {
                "status": "failed",
                "reason": f"override-invalid: {exc}",
                "current": str(current),
                "auto_eligible": False,
            }
        kind = version_kind(current, forced)
        if kind == "none":
            return {
                "status": "up-to-date",
                "reason": "forced-current",
                "current": str(current),
                "auto_eligible": False,
            }
        versions = iter_stable_manifest_versions(manifest)
        match = next((item for item in versions if item[0] == forced), None)
        if match is None:
            return {
                "status": "failed",
                "reason": "override-unavailable",
                "kind": kind,
                "candidate": str(forced),
                "current": str(current),
                "auto_eligible": False,
            }
        release_url = str(match[1].get("release_url") or "")
        if kind == "downgrade":
            return {
                "status": "review-required",
                "reason": "override-downgrade",
                "kind": kind,
                "candidate": str(forced),
                "current": str(current),
                "release_url": release_url,
                "auto_eligible": False,
            }
        if kind == "major" or (kind == "minor" and forced.minor != current.minor + 1):
            return {
                "status": "review-required",
                "reason": "override-out-of-policy",
                "kind": kind,
                "candidate": str(forced),
                "current": str(current),
                "release_url": release_url,
                "auto_eligible": False,
            }
        return {
            "status": "proposed" if kind == "patch" else "review-required",
            "reason": "manual-override",
            "kind": kind,
            "candidate": str(forced),
            "current": str(current),
            "release_url": release_url,
            "auto_eligible": kind == "patch",
        }

    versions = iter_stable_manifest_versions(manifest)
    series_now = (current.major, current.minor)
    series_next = (current.major, current.minor + 1)
    patch = newest_in_series(versions, series_now)
    if patch and patch[0] > current:
        return {
            "status": "proposed",
            "reason": "newer-patch",
            "kind": "patch",
            "candidate": str(patch[0]),
            "current": str(current),
            "release_url": str(patch[1].get("release_url") or ""),
            "auto_eligible": True,
        }
    minor = newest_in_series(versions, series_next)
    if not minor or not (minor[0] > current):
        return {"status": "up-to-date", "reason": "no-newer-stable", "current": str(current)}

    if ignore_soak:
        return {
            "status": "review-required",
            "reason": "next-minor",
            "kind": "minor",
            "candidate": str(minor[0]),
            "current": str(current),
            "release_url": str(minor[1].get("release_url") or ""),
            "auto_eligible": False,
        }

    published = parse_iso_date(
        str(minor[1].get("release_date") or minor[1].get("published_at") or "")
    )
    if published is None and callable(date_lookup):
        try:
            published = parse_iso_date(date_lookup(minor[0], minor[1]))
        except Exception:
            published = None
    if published is None:
        return {
            "status": "deferred",
            "reason": "release-date-unavailable",
            "kind": "minor",
            "candidate": str(minor[0]),
            "current": str(current),
            "auto_eligible": False,
        }
    age = (now - published).days
    if age < int(soak_days):
        return {
            "status": "deferred",
            "reason": f"soak ({age}/{soak_days} days)",
            "kind": "minor",
            "candidate": str(minor[0]),
            "current": str(current),
            "age_days": age,
            "auto_eligible": False,
        }
    return {
        "status": "review-required",
        "reason": "next-minor",
        "kind": "minor",
        "candidate": str(minor[0]),
        "current": str(current),
        "release_url": str(minor[1].get("release_url") or ""),
        "auto_eligible": False,
    }


def classify_python_change(current: str, candidate: str) -> dict[str, Any]:
    cur = parse_version(current)
    nxt = parse_version(candidate)
    kind = version_kind(cur, nxt)
    if kind == "none":
        return {"risk": "routine", "kind": kind, "auto_eligible": False, "reason": "no-change"}
    if kind == "downgrade":
        return {"risk": "review-required", "kind": kind, "auto_eligible": False, "reason": "downgrade"}
    if kind == "patch":
        return {"risk": "routine", "kind": kind, "auto_eligible": True, "reason": "stable-patch"}
    if kind == "minor":
        if nxt.major == cur.major and nxt.minor == cur.minor + 1:
            return {"risk": "review-required", "kind": kind, "auto_eligible": False, "reason": "next-minor"}
        return {"risk": "review-required", "kind": kind, "auto_eligible": False, "reason": "skip-minor-forbidden"}
    return {"risk": "review-required", "kind": kind, "auto_eligible": False, "reason": "major"}


_VERSION_TOKEN = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?(?:[a-zA-Z0-9_.-]*)?")


def _parse_dep_version(raw: str | None) -> tuple[int, ...] | None:
    if not raw:
        return None
    text = raw.strip().lstrip("vV")
    if PRERELEASE_RE.search(text):
        return None
    match = _VERSION_TOKEN.match(text)
    if not match:
        return None
    major, minor, patch = match.group(1), match.group(2), match.group(3) or "0"
    if not all(p.isdigit() for p in (major, minor, patch)):
        return None
    return (int(major), int(minor), int(patch))


def classify_package_update(old: str | None, new: str | None, *, name: str = "") -> dict[str, Any]:
    new_v = _parse_dep_version(new)
    old_v = _parse_dep_version(old)
    if new_v is None:
        return {"risk": "review-required", "reason": "unknown-or-prerelease", "auto_eligible": False, "name": name}
    if old_v is None:
        return {"risk": "review-required", "reason": "unknown-previous", "auto_eligible": False, "name": name}
    if new_v[0] != old_v[0]:
        return {"risk": "review-required", "reason": "package-major", "auto_eligible": False, "name": name}
    if old_v[0] == 0 and new_v[1] != old_v[1]:
        return {"risk": "review-required", "reason": "breaking-risk-0x-minor", "auto_eligible": False, "name": name}
    return {"risk": "routine", "reason": "package-patch-or-minor", "auto_eligible": True, "name": name}


def classify_action_update(
    old_ref: str | None,
    new_ref: str | None,
    *,
    old_action: str | None = None,
    new_action: str | None = None,
    comment_old: str | None = None,
    comment_new: str | None = None,
) -> dict[str, Any]:
    if (old_action or "") != (new_action or "") and new_action and old_action:
        return {"risk": "review-required", "reason": "new-or-moved-action", "auto_eligible": False}
    if not SHA_RE.fullmatch((new_ref or "").lower() if new_ref else ""):
        return {"risk": "review-required", "reason": "unpinned-or-floating-ref", "auto_eligible": False}
    old_major = _major_from_comment(comment_old)
    new_major = _major_from_comment(comment_new)
    if old_major is not None and new_major is not None and new_major != old_major:
        return {"risk": "review-required", "reason": "action-major", "auto_eligible": False}
    return {"risk": "routine", "reason": "action-pin-same-source", "auto_eligible": True}


def _major_from_comment(comment: str | None) -> int | None:
    if not comment:
        return None
    match = re.search(r"v(\d+)", comment)
    if not match:
        return None
    return int(match.group(1))


def highest_risk(members: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not members:
        return {"risk": "review-required", "reason": "empty-group", "auto_eligible": False}
    best = max(members, key=lambda m: RISK_RANK.get(str(m.get("risk") or "review-required"), 2))
    auto = all(bool(m.get("auto_eligible")) and m.get("risk") == "routine" for m in members)
    result = dict(best)
    result["auto_eligible"] = auto and result.get("risk") == "routine"
    result["members"] = len(members)
    return result


def auto_merge_enabled(value: str | None) -> bool:
    return (value or "").strip() == AUTO_YES


_ACTIONS_RUN_RE = re.compile(r"/actions/runs/(\d+)")


def _check_app_slug(run: Mapping[str, Any]) -> str:
    app = run.get("app") if isinstance(run.get("app"), dict) else {}
    return str(app.get("slug") or app.get("name") or run.get("app_slug") or "")


def _workflow_run_id_from_check(run: Mapping[str, Any]) -> int | None:
    raw = run.get("workflow_run_id")
    if raw not in (None, ""):
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
    html = str(run.get("html_url") or run.get("details_url") or "")
    match = _ACTIONS_RUN_RE.search(html)
    return int(match.group(1)) if match else None


def classify_checks(
    check_runs: Sequence[Mapping[str, Any]],
    *,
    expected_names: Sequence[str],
    head_sha: str,
    trusted_apps: Sequence[str] = ("github-actions", "github-actions[bot]"),
    legacy_statuses: Sequence[Mapping[str, Any]] | None = None,
    expected_workflow: str | None = None,
    workflow_runs: Sequence[Mapping[str, Any]] | None = None,
    expected_workflow_path: str | None = None,
    expected_workflow_id: int | None = None,
    workflow_jobs: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Require the trusted expected successful set on the exact head.

    Skipped, neutral, cancelled, pending, missing, unrelated, or foreign
    checks cannot satisfy a mandatory name. Zero checks is never ready.
    Missing SHA or app identity cannot satisfy a mandatory name. When
    ``expected_workflow`` is set, each required check must come from that
    trusted workflow's run on this head (name/path/id) *and* a matching
    successful job in that run. A familiar github-actions app/name or a
    separate green run does not authenticate every gate. Legacy Combined
    Status rows cannot satisfy a required check (never treated as success),
    but a SHA-bound pending/failed/error status for a required context
    still blocks even when expected-workflow jobs are green. Untrusted or
    stale status rows are ignored. Missing or truncated job evidence fails
    closed.
    """
    expected = [name for name in expected_names if name]
    if not expected:
        return {"state": "failed", "reason": "no-expected-checks"}
    if not SHA_RE.fullmatch((head_sha or "").lower()):
        return {"state": "failed", "reason": "missing-head-sha"}
    bound_run_ids: set[int] = set()
    if expected_workflow:
        if workflow_runs is None:
            return {"state": "failed", "reason": "missing-workflow-runs"}
        matching: list[Mapping[str, Any]] = []
        for run in workflow_runs:
            if not isinstance(run, dict):
                return {"state": "failed", "reason": "malformed-workflow-run"}
            name = str(run.get("name") or "")
            sha = str(run.get("head_sha") or run.get("sha") or "")
            path = str(run.get("path") or "")
            if name != expected_workflow:
                continue
            if sha != head_sha:
                continue
            if expected_workflow_path and path != expected_workflow_path:
                continue
            if expected_workflow_id is not None:
                try:
                    if int(run.get("id") or 0) != int(expected_workflow_id):
                        continue
                except (TypeError, ValueError):
                    continue
            matching.append(run)
        if not matching:
            return {"state": "failed", "reason": "missing-expected-workflow"}
        latest_wf = max(matching, key=lambda r: int(r.get("id") or 0))
        wf_status = str(latest_wf.get("status") or "")
        wf_conclusion = str(latest_wf.get("conclusion") or "")
        if wf_status != "completed":
            return {"state": "pending", "reason": "expected-workflow-pending"}
        if wf_conclusion != "success":
            return {"state": "failed", "reason": "expected-workflow-not-success"}
        try:
            bound_run_ids.add(int(latest_wf.get("id") or 0))
        except (TypeError, ValueError):
            return {"state": "failed", "reason": "missing-expected-workflow-id"}
        if not bound_run_ids or 0 in bound_run_ids:
            return {"state": "failed", "reason": "missing-expected-workflow-id"}
        if workflow_jobs is None:
            return {"state": "failed", "reason": "missing-workflow-jobs"}
        latest_jobs: dict[str, Mapping[str, Any]] = {}
        for job in workflow_jobs:
            if not isinstance(job, dict):
                return {"state": "failed", "reason": "malformed-workflow-job"}
            jname = str(job.get("name") or "")
            jsha = str(job.get("head_sha") or job.get("sha") or "")
            if jsha != head_sha:
                continue
            try:
                jrun = int(job.get("run_id") or 0)
            except (TypeError, ValueError):
                jrun = 0
            if jrun not in bound_run_ids:
                continue
            previous = latest_jobs.get(jname)
            if previous is None:
                latest_jobs[jname] = job
                continue
            prev_id = int(previous.get("id") or 0)
            new_id = int(job.get("id") or 0)
            if new_id >= prev_id:
                latest_jobs[jname] = job
        for name in expected:
            job = latest_jobs.get(name)
            if job is None:
                reason = (
                    "missing-security-evidence"
                    if "security" in name.lower()
                    else "missing-mandatory-job"
                )
                return {"state": "failed", "reason": reason, "missing": name}
            jstatus = str(job.get("status") or "")
            jconclusion = str(job.get("conclusion") or "")
            if jstatus != "completed":
                return {
                    "state": "pending",
                    "reason": "mandatory-job-pending",
                    "missing": name,
                }
            if jconclusion != "success":
                reason = (
                    "security-job-not-success"
                    if "security" in name.lower()
                    else "mandatory-job-not-success"
                )
                return {"state": "failed", "reason": reason, "missing": name}

    latest: dict[str, Mapping[str, Any]] = {}
    for run in check_runs or []:
        if not isinstance(run, dict):
            return {"state": "failed", "reason": "malformed-check"}
        name = str(run.get("name") or "")
        sha = str(run.get("head_sha") or run.get("sha") or "")
        if sha != head_sha:
            continue
        slug = _check_app_slug(run)
        if name in expected:
            if not slug:
                continue
            if trusted_apps and slug not in trusted_apps:
                return {"state": "failed", "reason": f"untrusted-app:{name}:{slug}"}
        if bound_run_ids:
            run_id = _workflow_run_id_from_check(run)
            if run_id not in bound_run_ids:
                continue
        previous = latest.get(name)
        if previous is None:
            latest[name] = run
            continue
        prev_id = int(previous.get("id") or 0)
        new_id = int(run.get("id") or 0)
        if new_id >= prev_id:
            latest[name] = run

    outcomes: dict[str, str] = {}
    for name in expected:
        run = latest.get(name)
        if run is None:
            outcomes[name] = "missing"
            continue
        status = str(run.get("status") or "")
        conclusion = str(run.get("conclusion") or "")
        if status != "completed":
            outcomes[name] = status or "pending"
        elif conclusion == "success":
            outcomes[name] = "success"
        else:
            outcomes[name] = conclusion or "unknown"

    if legacy_statuses:
        for status in legacy_statuses:
            if not isinstance(status, dict):
                return {"state": "failed", "reason": "malformed-legacy-status"}
            name = str(status.get("context") or status.get("name") or "")
            if name not in expected:
                continue
            sha = str(status.get("sha") or status.get("head_sha") or "")
            if sha != head_sha:
                continue
            creator = status.get("creator") if isinstance(status.get("creator"), dict) else {}
            creator_login = str(
                creator.get("login") or status.get("creator_login") or status.get("app_slug") or ""
            )
            if creator_login and trusted_apps and creator_login not in trusted_apps:
                continue
            state = str(status.get("state") or "").lower()
            if state in {"success", "ok"}:
                continue
            if state in {"pending", "expected"}:
                outcomes[name] = "pending"
            else:
                outcomes[name] = state or "failed"

    if any(v == "missing" for v in outcomes.values()):
        return {"state": "failed", "reason": "missing-mandatory-check", "checks": outcomes}
    if any(v in {"pending", "queued", "in_progress"} for v in outcomes.values()):
        return {"state": "pending", "reason": "mandatory-check-pending", "checks": outcomes}
    if any(v != "success" for v in outcomes.values()):
        return {"state": "failed", "reason": "mandatory-check-not-success", "checks": outcomes}
    return {"state": "ready", "reason": "expected-set-green", "checks": outcomes}


WORKFLOW_POLICY_HINTS = (
    "on:", "permissions:", "runs-on:", "timeout-minutes:", "cancel-in-progress:",
    "pull_request_target", "workflow_dispatch", "schedule:", "secrets.",
)
WORKFLOW_RUN_HINT = re.compile(r"^\s+run:\s*", re.M)


def diff_touches_workflow_policy(patch: str) -> bool:
    if not patch:
        return False
    lowered = patch.lower()
    if any(hint.lower() in lowered for hint in WORKFLOW_POLICY_HINTS if hint != "on:"):
        # Only count added/removed policy lines, not context.
        for line in patch.splitlines():
            if not (line.startswith("+") or line.startswith("-")) or line.startswith("+++") or line.startswith("---"):
                continue
            body = line[1:]
            if WORKFLOW_RUN_HINT.match(body) or any(
                body.strip().startswith(h.rstrip(":")) or h in body for h in (
                    "permissions:", "timeout-minutes:", "cancel-in-progress:",
                    "pull_request_target", "workflow_dispatch", "schedule:",
                )
            ):
                return True
            if "secrets." in body or "persist-credentials" in body:
                return True
    return False


def validate_diff(
    files: Sequence[Mapping[str, Any]],
    *,
    allowed_files: Sequence[str],
    kind: str,
) -> dict[str, Any]:
    """Structural diff validation. Filename alone does not make a workflow change routine."""
    allowed = set(allowed_files)
    unexpected: list[str] = []
    for item in files:
        name = str(item.get("filename") or item.get("path") or "")
        if name not in allowed:
            unexpected.append(name)
            continue
        patch = str(item.get("patch") or "")
        if name.endswith((".yml", ".yaml")) and kind in {"dependabot-actions", "python-bump"}:
            if diff_touches_workflow_policy(patch):
                return {
                    "ok": False,
                    "reason": "workflow-policy-change",
                    "file": name,
                }
        if kind == "python-bump" and name != ".python-version" and name not in allowed:
            unexpected.append(name)
    if unexpected:
        return {"ok": False, "reason": "unexpected-path", "files": unexpected}
    return {"ok": True, "reason": "approved-paths"}


_DECISION_REVIEW_STATES = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}


def effective_reviews(reviews: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Newest *decision* per user. COMMENTED/PENDING never clear a change request."""
    latest: dict[str, Mapping[str, Any]] = {}
    for index, review in enumerate(reviews or []):
        if not isinstance(review, dict):
            continue
        state = str(review.get("state") or "")
        if state not in _DECISION_REVIEW_STATES:
            continue
        user = review.get("user") if isinstance(review.get("user"), dict) else {}
        login = str(user.get("login") or "") or f"anon-{review.get('id') or index}"
        rid = int(review.get("id") or 0)
        submitted = str(review.get("submitted_at") or "")
        previous = latest.get(login)
        if previous is None:
            latest[login] = review
            continue
        prev_id = int(previous.get("id") or 0)
        if rid > prev_id:
            latest[login] = review
        elif rid == prev_id and submitted >= str(previous.get("submitted_at") or ""):
            latest[login] = review
    return list(latest.values())


def review_blocks(pr: Mapping[str, Any], reviews: Sequence[Mapping[str, Any]], hold_labels: Sequence[str]) -> str | None:
    if pr.get("draft") is True:
        return "draft"
    if str(pr.get("state") or "") != "open":
        return f"state:{pr.get('state')}"
    labels = []
    for label in pr.get("labels") or []:
        if isinstance(label, dict):
            labels.append(str(label.get("name") or "").lower())
        else:
            labels.append(str(label).lower())
    for hold in hold_labels:
        if hold.lower() in labels:
            return f"hold-label:{hold}"
    for review in effective_reviews(reviews):
        state = str(review.get("state") or "")
        if state == "CHANGES_REQUESTED":
            return "changes-requested"
    return None


def _commit_logins(commits: Sequence[Mapping[str, Any]] | None) -> set[str] | None:
    if commits is None:
        return None
    logins: set[str] = set()
    for commit in commits:
        if not isinstance(commit, dict):
            continue
        for role in ("author", "committer"):
            node = commit.get(role) if isinstance(commit.get(role), dict) else {}
            login = str(node.get("login") or "")
            if login:
                logins.add(login)
        inner = commit.get("commit") if isinstance(commit.get("commit"), dict) else {}
        for role in ("author", "committer"):
            node = inner.get(role) if isinstance(inner.get(role), dict) else {}
            name = str(node.get("name") or "")
            if name == "github-actions[bot]":
                logins.add("github-actions[bot]")
    return logins


def trusted_updater(
    pr: Mapping[str, Any],
    identities: Mapping[str, Any],
    *,
    commits: Sequence[Mapping[str, Any]] | None = None,
) -> str | None:
    """Identify a trusted updater. github-actions[bot] as commit author alone is not enough."""
    user = pr.get("user") if isinstance(pr.get("user"), dict) else {}
    login = str(user.get("login") or "")
    head_ref = str((pr.get("head") or {}).get("ref") or "")
    if login == str(identities.get("dependabot", {}).get("login") or "dependabot[bot]"):
        return "dependabot"
    bump = identities.get("python_bump") or {}
    prefix = str(bump.get("branch_prefix") or "chore/python-")
    bot = str(bump.get("login") or "github-actions[bot]")
    allowed_pr = {str(item) for item in (bump.get("allowed_pr_logins") or []) if item}
    if not head_ref.startswith(prefix):
        return None
    if login == bot or login in allowed_pr:
        return "python_bump"
    commit_logins = _commit_logins(commits)
    if commit_logins is not None and commit_logins and commit_logins <= {bot}:
        return "python_bump"
    return None


def decide_merge(snapshot: Mapping[str, Any]) -> Decision:
    """Pure merge decision. Missing fields fail closed. Never writes."""
    required = ("repository", "pull_request", "checks", "policy", "head_sha")
    for key in required:
        if key not in snapshot:
            return Decision("fail", f"missing-field:{key}")

    policy = snapshot["policy"]
    if not isinstance(policy, dict):
        return Decision("fail", "malformed-policy")
    pr = snapshot["pull_request"]
    if not isinstance(pr, dict):
        return Decision("fail", "malformed-pull-request")

    expected_repo = str(policy.get("repository") or snapshot["repository"])
    default_branch = str(policy.get("default_branch") or "main")
    base = pr.get("base") if isinstance(pr.get("base"), dict) else {}
    if str(base.get("ref") or "") != default_branch:
        return Decision("defer", "unexpected-base", risk="blocked")
    if str(snapshot["repository"]) != expected_repo:
        return Decision("fail", "unexpected-repository")

    association = maintenance_common.repo_association_failure(pr, expected_repo)
    if association:
        return Decision("fail", association, risk="blocked")

    identities = policy.get("updater_identities") or {}
    kind = trusted_updater(pr, identities, commits=snapshot.get("commits"))
    if kind is None:
        return Decision("defer", "untrusted-updater", risk="blocked")

    hold = review_blocks(pr, snapshot.get("reviews") or [], policy.get("human_review_labels") or HOLD_LABELS_FALLBACK)
    if hold:
        return Decision("defer", hold, risk="blocked")

    head_sha = str(snapshot["head_sha"])
    pr_head = str((pr.get("head") or {}).get("sha") or "")
    if pr_head != head_sha:
        return Decision("fail", "head-changed", risk="blocked")

    files = snapshot.get("files") or []
    allowed = list((identities.get(kind) or {}).get("allowed_files") or policy.get("allowed_files") or [])
    if kind == "dependabot":
        allowed = list(policy.get("dependabot_allowed_files") or allowed or DEFAULT_DEPENDABOT_ALLOWED)
        if not allowed:
            return Decision("fail", "empty-allowlist")
        wf_allowed = list(
            policy.get("dependabot_actions_allowed_files") or DEFAULT_DEPENDABOT_ACTIONS_ALLOWED
        )
        if wf_allowed and any(
            str(item.get("filename") or "").startswith(".github/workflows/")
            for item in files if isinstance(item, dict)
        ):
            allowed = list(dict.fromkeys([*allowed, *wf_allowed]))
    elif kind == "python_bump":
        allowed = list((identities.get("python_bump") or {}).get("allowed_files") or [".python-version"])
    diff_kind = "python-bump" if kind == "python_bump" else str(snapshot.get("diff_kind") or "dependabot")
    if kind == "dependabot" and any(
        str(item.get("filename") or "").startswith(".github/workflows/")
        for item in files if isinstance(item, dict)
    ):
        diff_kind = "dependabot-actions"
    diff = validate_diff(files, allowed_files=allowed, kind=diff_kind)
    if not diff.get("ok"):
        return Decision("review-required", str(diff.get("reason") or "diff"), risk="review-required")

    expected = list(policy.get("mandatory_check_names") or [])
    expected_workflow = str(policy.get("ci_workflow_name") or "") or None
    expected_workflow_path = str(policy.get("ci_workflow_path") or "") or None
    classified = classify_checks(
        snapshot["checks"] if isinstance(snapshot["checks"], list) else [],
        expected_names=expected,
        head_sha=head_sha,
        legacy_statuses=snapshot.get("legacy_statuses") or [],
        expected_workflow=expected_workflow,
        workflow_runs=snapshot.get("workflow_runs") if expected_workflow else None,
        expected_workflow_path=expected_workflow_path,
        workflow_jobs=snapshot.get("workflow_jobs") if expected_workflow else None,
    )
    if classified.get("state") != "ready":
        action = "defer" if classified.get("state") == "pending" else "fail"
        return Decision(action, str(classified.get("reason") or "checks"), risk="blocked", checks=classified.get("checks") or {})

    producers_policy = policy.get("check_producers") or {}
    if producers_policy:
        producers = maintenance_common.verify_check_producers(
            snapshot.get("producer_evidence"),
            expected_names=expected,
            head_sha=head_sha,
            producers=producers_policy,
            repository=expected_repo,
        )
        if producers.get("state") != "ready":
            return Decision(
                "fail",
                str(producers.get("reason") or "producers"),
                risk="blocked",
                checks=classified.get("checks") or {},
            )

    required_security = list(policy.get("required_security_evidence") or [])
    security_mode = str(policy.get("security_evidence_mode") or "")
    if security_mode or required_security:
        security = maintenance_common.verify_security_evidence(
            snapshot.get("security_evidence"),
            required_security,
            mode=security_mode,
        )
        if security.get("state") == "failed":
            return Decision(
                "fail",
                str(security.get("reason") or "security-evidence"),
                risk="blocked",
                checks=classified.get("checks") or {},
            )
        if security.get("state") != "ready":
            return Decision(
                "defer",
                str(security.get("reason") or "security-evidence-unavailable"),
                risk="blocked",
                checks=classified.get("checks") or {},
            )

    derived_candidate = maintenance_common.candidate_version_from_files(
        snapshot.get("files") if isinstance(snapshot.get("files"), list) else []
    )
    supplied_candidate = str(snapshot.get("candidate_version") or "") or None
    candidate_version = derived_candidate
    if kind == "python_bump":
        if not derived_candidate:
            return Decision(
                "fail",
                "candidate-version-unparsed",
                risk="blocked",
                checks=classified.get("checks") or {},
            )
        if supplied_candidate and supplied_candidate != derived_candidate:
            return Decision(
                "fail",
                "candidate-version-mismatch",
                risk="blocked",
                checks=classified.get("checks") or {},
            )

    pub_evidence = snapshot.get("publication_evidence") if isinstance(snapshot.get("publication_evidence"), dict) else {}
    if kind == "python_bump" and isinstance(pub_evidence, dict) and pub_evidence.get("error"):
        return Decision(
            "fail",
            str(pub_evidence.get("error") or "publication-collection-failed"),
            risk="blocked",
            checks=classified.get("checks") or {},
        )
    publication = maintenance_common.verify_publication_gate(
        mode=str(policy.get("publication_evidence_mode") or ""),
        kind=kind,
        evidence=pub_evidence,
        pr=pr,
        candidate_version=candidate_version,
        trusted_proposer_path=str(policy.get("publication_proposer_workflow") or maintenance_common.DEFAULT_PROPOSER_PATH),
        proposal_files=list(policy.get("publication_proposal_files") or maintenance_common.DEFAULT_PROPOSAL_FILES),
        pinned_pip=str(policy.get("pinned_pip") or maintenance_common.PINNED_PIP),
        pinned_pip_tools=str(policy.get("pinned_pip_tools") or maintenance_common.PINNED_PIP_TOOLS),
        repository=expected_repo,
    )
    if publication.get("state") != "ready":
        action = "defer" if publication.get("state") == "pending" else "fail"
        return Decision(
            action,
            str(publication.get("reason") or "publication-evidence"),
            risk="blocked",
            checks=classified.get("checks") or {},
        )

    files = snapshot.get("files") if isinstance(snapshot.get("files"), list) else []
    computed = snapshot_risk_from_files(files, diff_kind)
    meta = snapshot.get("risk") if isinstance(snapshot.get("risk"), dict) else {}
    risk_info = highest_risk(
        [
            computed,
            {
                "risk": str(meta.get("risk") or "review-required"),
                "auto_eligible": bool(meta.get("auto_eligible")),
                "reason": str(meta.get("reason") or "metadata"),
                "members": int(meta.get("members") or 0),
            },
        ]
    )
    risk = str(risk_info.get("risk") or "review-required")
    auto_eligible = bool(risk_info.get("auto_eligible"))
    if risk != "routine" or not auto_eligible:
        return Decision("review-required", str(risk_info.get("reason") or risk), risk=risk, checks=classified.get("checks") or {})

    env_vars = snapshot.get("variables") or {}
    flag_name = str((identities.get(kind) or {}).get("auto_merge_var") or "")
    if not auto_merge_enabled(str(env_vars.get(flag_name) or "")):
        return Decision("defer", f"{flag_name}-disabled", risk="routine", checks=classified.get("checks") or {})

    mergeable = pr.get("mergeable")
    mergeable_state = str(pr.get("mergeable_state") or "")
    if mergeable is None or mergeable_state in {"unknown", ""}:
        return Decision("defer", "mergeability-unknown", risk="routine", checks=classified.get("checks") or {})
    if mergeable is False or mergeable_state in {"dirty", "blocked", "draft"}:
        return Decision("fail", f"not-mergeable:{mergeable_state}", risk="blocked", checks=classified.get("checks") or {})
    if mergeable is not True:
        return Decision("fail", f"not-mergeable:{mergeable_state}", risk="blocked")

    method = str(policy.get("allowed_merge_method") or "squash")
    return Decision(
        "merge",
        "gates-passed",
        risk="routine",
        merge_method=method,
        checks=classified.get("checks") or {},
        pr_url=str(pr.get("html_url") or "") or None,
    )


def lock_digest(path: str | os.PathLike) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def production_manifest(root: str | os.PathLike, files: Sequence[str]) -> dict[str, str]:
    base = Path(root)
    out: dict[str, str] = {}
    for rel in files:
        path = base / rel
        if not path.is_file():
            continue
        out[rel.replace("\\", "/")] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def normalize_compile_header(text: str, python_series: str = "3.14") -> str:
    """Normalize only the pip-compile Python version in the generated header.

    Index URLs, constraints, markers, via-comments, and pin/hash lines are
    compared as-is. A rebuilt interpreter patch in the header may pass;
    changing those other directives without a pin change must not.
    """
    return re.sub(r"with Python \d+\.\d+(?:\.\d+)?", f"with Python {python_series}", text)


def file_is_optional_doc(rel: str, profile: Mapping[str, Any]) -> bool:
    optional = list(profile.get("optional_docs") or [])
    rel_n = rel.replace("\\", "/")
    if rel_n in optional:
        return True
    if rel_n.startswith("docs/") or rel_n.startswith("docs\\"):
        return True
    return False


def _github_json(url: str, token: str, method: str = "GET", body: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2026-03-10")
    req.add_header("User-Agent", "news-express-maintenance")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read()
            parsed = json.loads(payload.decode("utf-8")) if payload else {}
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read() if hasattr(exc, "read") else b""
        try:
            parsed = json.loads(raw.decode("utf-8")) if raw else {"message": str(exc)}
        except json.JSONDecodeError:
            parsed = {"message": raw.decode("utf-8", "replace")}
        return exc.code, parsed
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return 0, {"message": str(exc)}


def _load_fixture(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("fixture must be a JSON object")
    return data


def cmd_decide(args: argparse.Namespace) -> int:
    if not args.fixture:
        print("decision mode requires --fixture; refusing live GitHub fallback", file=sys.stderr)
        return 2
    snapshot = _load_fixture(args.fixture)
    decision = decide_merge(snapshot)
    json.dump(decision.to_json(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    if args.apply:
        print("refusing --apply with --fixture (no writes in decision fixtures)", file=sys.stderr)
        return 2
    return 0 if decision.action != "fail" else 1


def cmd_select(args: argparse.Namespace) -> int:
    fixture = _load_fixture(args.fixture) if args.fixture else None
    if fixture is None:
        print("select requires --fixture in this mode", file=sys.stderr)
        return 2
    current = parse_version(str(fixture.get("current") or ""))
    manifest = fixture.get("manifest") or []
    result = select_python_candidate(
        current,
        manifest,
        soak_days=int(fixture.get("soak_days") or 30),
        now=parse_iso_date(fixture.get("now")) or datetime.now(timezone.utc),
        ignore_soak=bool(fixture.get("ignore_soak")),
        force=fixture.get("force"),
    )
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def cmd_classify_checks(args: argparse.Namespace) -> int:
    fixture = _load_fixture(args.fixture)
    result = classify_checks(
        fixture.get("check_runs") or [],
        expected_names=fixture.get("expected_names") or [],
        head_sha=str(fixture.get("head_sha") or ""),
        trusted_apps=fixture.get("trusted_apps") or ("github-actions", "github-actions[bot]"),
        legacy_statuses=fixture.get("legacy_statuses") or [],
        expected_workflow=fixture.get("expected_workflow"),
        workflow_runs=fixture.get("workflow_runs"),
        expected_workflow_path=fixture.get("expected_workflow_path"),
        expected_workflow_id=fixture.get("expected_workflow_id"),
        workflow_jobs=fixture.get("workflow_jobs"),
    )
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if result.get("state") == "ready" else 1


def _with_page(url: str, page: int) -> str:
    if re.search(r"[?&]page=", url):
        return re.sub(r"([?&]page=)\d+", rf"\g<1>{page}", url)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}page={page}"


def _api_pages(url: str, token: str, *, max_pages: int = 10) -> tuple[int, Any]:
    """Paginate list or nested GitHub collection endpoints. Truncation fails closed."""
    items: list[Any] = []
    total: int | None = None
    for page in range(1, max_pages + 1):
        status, payload = _github_json(_with_page(url, page), token)
        if status != 200:
            return status, payload
        batch: list[Any]
        if isinstance(payload, list):
            batch = payload
        elif isinstance(payload, dict) and isinstance(payload.get("check_runs"), list):
            batch = payload["check_runs"]
            total = int(payload.get("total_count") or 0)
        elif isinstance(payload, dict) and isinstance(payload.get("workflow_runs"), list):
            batch = payload["workflow_runs"]
            total = int(payload.get("total_count") or 0)
        elif isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
            batch = payload["jobs"]
            total = int(payload.get("total_count") or 0)
        elif isinstance(payload, dict) and isinstance(payload.get("statuses"), list):
            batch = payload["statuses"]
            total = int(payload.get("total_count") or 0)
        else:
            return 0, {"message": "unexpected-list-payload"}
        items.extend(batch)
        if total is not None:
            if len(items) >= total:
                return 200, items
            if not batch:
                return 0, {"message": "pagination-truncated", "count": len(items), "total": total}
            continue
        if len(batch) < 100:
            return 200, items
    return 0, {"message": "pagination-truncated", "count": len(items), "total": total}


def build_live_snapshot(event: Mapping[str, Any], token: str, profile: Mapping[str, Any]) -> dict[str, Any] | Decision:
    repo = event.get("repository") if isinstance(event.get("repository"), dict) else {}
    full_name = str(repo.get("full_name") or os.environ.get("GITHUB_REPOSITORY") or "")
    if "/" not in full_name:
        return Decision("fail", "missing-repository")
    owner, name = full_name.split("/", 1)
    default_branch = str(repo.get("default_branch") or "main")
    pr_number = None
    head_sha = ""
    if event.get("pull_request"):
        pr_number = (event.get("pull_request") or {}).get("number")
        head_sha = str(((event.get("pull_request") or {}).get("head") or {}).get("sha") or "")
    elif event.get("workflow_run"):
        wr = event["workflow_run"]
        head_sha = str(wr.get("head_sha") or "")
        pulls = wr.get("pull_requests") or []
        if pulls and isinstance(pulls[0], dict):
            pr_number = pulls[0].get("number")
    elif event.get("check_suite"):
        head_sha = str((event.get("check_suite") or {}).get("head_sha") or "")
        pulls = (event.get("check_suite") or {}).get("pull_requests") or []
        if pulls and isinstance(pulls[0], dict):
            pr_number = pulls[0].get("number")
    if not pr_number:
        return Decision("defer", "no-associated-pr")
    status, pr = _github_json(f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}", token)
    if status != 200 or not isinstance(pr, dict):
        return Decision("fail", f"pr-api:{status}")
    head_sha = str((pr.get("head") or {}).get("sha") or head_sha)
    status, check_runs = _api_pages(
        f"https://api.github.com/repos/{owner}/{name}/commits/{head_sha}/check-runs?per_page=100&filter=latest",
        token,
    )
    if status != 200 or not isinstance(check_runs, list):
        return Decision("fail", f"checks-api:{status}")
    mandatory = list(profile.get("mandatory_check_names") or [])

    def _get_json(url: str) -> tuple[int, Any]:
        return _github_json(url, token)

    def _get_pages(url: str) -> tuple[int, Any]:
        return _api_pages(url, token)

    producer_evidence = maintenance_common.collect_producer_evidence(
        owner, name, check_runs, mandatory, _get_json
    )
    _security_mode, required_security = maintenance_common.security_policy(profile)
    head_ref = str((pr.get("head") or {}).get("ref") or "")
    security_evidence = maintenance_common.collect_security_evidence(
        owner, name, head_sha, required_security, _get_pages, ref=head_ref
    )
    pub_mode, pub_path, pub_files = maintenance_common.publication_policy(profile)
    status, files = _api_pages(
        f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}/files?per_page=100",
        token,
    )
    if status != 200 or not isinstance(files, list):
        return Decision("fail", f"files-api:{status}")
    status, reviews = _api_pages(
        f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}/reviews?per_page=100",
        token,
    )
    if status != 200 or not isinstance(reviews, list):
        return Decision("fail", f"reviews-api:{status}")
    status, legacy = _api_pages(
        f"https://api.github.com/repos/{owner}/{name}/commits/{head_sha}/statuses?per_page=100",
        token,
    )
    if status != 200 or not isinstance(legacy, list):
        return Decision("fail", f"statuses-api:{status}")
    status, workflow_runs = _api_pages(
        f"https://api.github.com/repos/{owner}/{name}/actions/runs?head_sha={head_sha}&per_page=100",
        token,
    )
    if status != 200 or not isinstance(workflow_runs, list):
        return Decision("fail", f"workflow-runs-api:{status}")
    status, commits = _api_pages(
        f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}/commits?per_page=100",
        token,
    )
    if status != 200 or not isinstance(commits, list):
        return Decision("fail", f"commits-api:{status}")
    workflow_jobs: list[Any] = []
    expected_name = str(profile.get("ci_workflow_name") or "")
    expected_path = str(profile.get("ci_workflow_path") or "")
    if expected_name:
        matching: list[Mapping[str, Any]] = []
        for run in workflow_runs:
            if not isinstance(run, dict):
                return Decision("fail", "malformed-workflow-run")
            if str(run.get("name") or "") != expected_name:
                continue
            if str(run.get("head_sha") or run.get("sha") or "") != head_sha:
                continue
            if expected_path and str(run.get("path") or "") != expected_path:
                continue
            matching.append(run)
        if matching:
            latest_wf = max(matching, key=lambda r: int(r.get("id") or 0))
            try:
                rid = int(latest_wf.get("id") or 0)
            except (TypeError, ValueError):
                rid = 0
            if not rid:
                return Decision("fail", "missing-expected-workflow-id")
            status, workflow_jobs = _api_pages(
                f"https://api.github.com/repos/{owner}/{name}/actions/runs/{rid}/jobs?per_page=100",
                token,
            )
            if status != 200 or not isinstance(workflow_jobs, list):
                return Decision("fail", f"workflow-jobs-api:{status}")
        else:
            workflow_jobs = []
    identities = profile.get("updater_identities") or {}
    kind = trusted_updater(pr, identities, commits=commits)
    risk = snapshot_risk_from_files(files, kind_hint=kind)
    if kind == "python_bump":
        allowed = list((identities.get("python_bump") or {}).get("allowed_files") or [".python-version"])
    else:
        allowed = list(profile.get("dependabot_allowed_files") or DEFAULT_DEPENDABOT_ALLOWED)
    pinned_pip, pinned_tools = maintenance_common.compiler_pins(profile)
    publication_block = profile.get("publication_evidence") if isinstance(profile.get("publication_evidence"), dict) else {}
    expected_commit = str(publication_block.get("commit_identity") or "")
    publication_evidence: dict[str, Any] = {}
    candidate_version = maintenance_common.candidate_version_from_files(files if isinstance(files, list) else [])
    if kind == "python_bump" and pub_mode == "required":
        publication_evidence = maintenance_common.collect_publication_evidence(
            owner,
            name,
            pr,
            files if isinstance(files, list) else [],
            get_json=_get_json,
            get_pages=_get_pages,
            trusted_proposer_path=pub_path,
            proposal_files=pub_files,
            expected_commit_identity=expected_commit,
        )
        if not candidate_version:
            candidate_version = publication_evidence.get("candidate_version")
    return {
        "repository": full_name,
        "head_sha": head_sha,
        "pull_request": pr,
        "checks": check_runs,
        "producer_evidence": producer_evidence,
        "security_evidence": security_evidence,
        "publication_evidence": publication_evidence,
        "candidate_version": candidate_version,
        "files": files,
        "reviews": reviews,
        "legacy_statuses": legacy,
        "workflow_runs": workflow_runs,
        "workflow_jobs": workflow_jobs,
        "commits": commits,
        "risk": risk,
        "allowed_files": allowed,
        "diff_kind": "python-bump" if kind == "python_bump" else "dependabot",
        "variables": {
            "AUTO_MERGE_DEPENDABOT": os.environ.get("AUTO_MERGE_DEPENDABOT", ""),
            "AUTO_MERGE_PYTHON_BUMP": os.environ.get("AUTO_MERGE_PYTHON_BUMP", ""),
        },
        "policy": {
            "repository": full_name,
            "default_branch": default_branch,
            "mandatory_check_names": profile.get("mandatory_check_names") or [],
            "ci_workflow_name": profile.get("ci_workflow_name") or "",
            "ci_workflow_path": profile.get("ci_workflow_path") or "",
            "check_producers": profile.get("check_producers") or {},
            "security_evidence_mode": _security_mode,
            "required_security_evidence": required_security,
            "publication_evidence_mode": pub_mode,
            "publication_proposer_workflow": pub_path,
            "publication_proposal_files": list(pub_files),
            "pinned_pip": pinned_pip,
            "pinned_pip_tools": pinned_tools,
            "human_review_labels": profile.get("human_review_labels") or list(HOLD_LABELS_FALLBACK),
            "updater_identities": identities,
            "allowed_merge_method": profile.get("allowed_merge_method") or "squash",
            "dependabot_allowed_files": list(profile.get("dependabot_allowed_files") or DEFAULT_DEPENDABOT_ALLOWED),
            "dependabot_actions_allowed_files": list(
                profile.get("dependabot_actions_allowed_files") or DEFAULT_DEPENDABOT_ACTIONS_ALLOWED
            ),
        },
    }


_REQ_EQ = re.compile(r"^([A-Za-z0-9_.-]+)==([^\\\s#;]+)")
_REQ_FILES = {
    "requirements.txt", "requirements.in", "requirements-dev.txt", "requirements-dev.in",
}
_REQ_POLICY_PREFIX = re.compile(
    r"^(?:"
    r"--(?:extra-index-url|index-url|find-links|trusted-host|no-index|"
    r"pre|no-binary|only-binary|constraint|editable|hash)\b"
    r"|-(?:i|f|c|e)\b"
    r")"
)
_REQ_VCS_OR_URL = re.compile(
    r"^(?:git\+|hg\+|svn\+|bzr\+|ssh://|git://|https?://|file:)",
    re.IGNORECASE,
)


def _norm_pkg(name: str) -> str:
    return name.replace("_", "-").lower()


def _requirement_policy_reason(body: str) -> str | None:
    """Classify a significant requirements line that is not a plain pin."""
    stripped = body.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("--hash="):
        return None
    first = stripped.split()[0]
    if _REQ_POLICY_PREFIX.match(stripped):
        if first.startswith("--hash"):
            return "hash-directive"
        if first in {"-c", "--constraint"} or first.startswith("-c"):
            return "constraint-file"
        return "unexpected-index-or-source"
    if _REQ_VCS_OR_URL.match(stripped) or " @" in f" {stripped}" or stripped.startswith("@"):
        return "direct-or-vcs-url"
    if "[" in stripped and "]" in stripped:
        return "extras-change"
    if ";" in stripped:
        return "environment-marker"
    if _REQ_EQ.match(stripped) or re.match(r"^([A-Za-z0-9_.-]+)[<>=!~]", stripped):
        return None
    return "unparsed-requirement-line"


def requirement_policy_members(patch: str) -> list[dict[str, Any]]:
    """One review-required member per significant non-pin requirements line."""
    members: list[dict[str, Any]] = []
    for raw in patch.splitlines():
        if raw.startswith("---") or raw.startswith("+++"):
            continue
        if not (raw.startswith("-") or raw.startswith("+")):
            continue
        body = raw[1:].strip()
        reason = _requirement_policy_reason(body)
        if reason is None:
            continue
        members.append(
            {
                "risk": "review-required",
                "auto_eligible": False,
                "reason": reason,
                "line": body[:160],
            }
        )
    return members


def requirement_hash_members(patch: str) -> list[dict[str, Any]]:
    """Associate +/- hash lines with the current package block.

    Hash regeneration on a version change is expected. Hash edits on a
    package whose version did not change, reordered hash lists, and hash
    lines with no package context require review.
    """
    current: str | None = None
    versions: dict[str, dict[str, str]] = {}
    hashes_old: dict[str, list[str]] = {}
    hashes_new: dict[str, list[str]] = {}
    unassociated = False
    for raw in patch.splitlines():
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("@@"):
            current = None
            continue
        if not raw or raw[0] not in "+- ":
            continue
        kind = raw[0]
        body = raw[1:].strip().rstrip("\\").strip()
        if not body or body.startswith("#"):
            continue
        if body.startswith("--hash="):
            if current is None:
                if kind in "+-":
                    unassociated = True
                continue
            if kind == "-":
                hashes_old.setdefault(current, []).append(body)
            elif kind == "+":
                hashes_new.setdefault(current, []).append(body)
            continue
        match = _REQ_EQ.match(body)
        if not match:
            continue
        current = _norm_pkg(match.group(1))
        ver = match.group(2)
        slot = versions.setdefault(current, {})
        if kind == "-":
            slot["old"] = ver
        elif kind == "+":
            slot["new"] = ver
        else:
            slot.setdefault("old", ver)
            slot.setdefault("new", ver)
    members: list[dict[str, Any]] = []
    if unassociated:
        members.append({
            "risk": "review-required",
            "auto_eligible": False,
            "reason": "hash-only",
        })
    for pkg in sorted(set(hashes_old) | set(hashes_new)):
        vers = versions.get(pkg) or {}
        old_v, new_v = vers.get("old"), vers.get("new")
        if old_v and new_v and old_v != new_v:
            continue
        if hashes_old.get(pkg) != hashes_new.get(pkg):
            members.append({
                "risk": "review-required",
                "auto_eligible": False,
                "reason": "unchanged-version-hash-mutation",
                "name": pkg,
            })
    return members


def parse_requirement_version_maps(patch: str) -> tuple[dict[str, str], dict[str, str], bool, bool]:
    """Map every package old/new version in a unified diff. Last-pair overwrite is forbidden."""
    old: dict[str, str] = {}
    new: dict[str, str] = {}
    saw_hash = False
    saw_pkg = False
    for raw in patch.splitlines():
        if raw.startswith("---") or raw.startswith("+++"):
            continue
        if not (raw.startswith("-") or raw.startswith("+")):
            continue
        body = raw[1:].strip()
        if not body or body.startswith("#"):
            continue
        if "--hash=" in body:
            saw_hash = True
            continue
        match = _REQ_EQ.match(body)
        if not match:
            range_match = re.match(r"^([A-Za-z0-9_.-]+)[<>=!~]", body)
            if range_match:
                saw_pkg = True
                name = _norm_pkg(range_match.group(1))
                if raw.startswith("-"):
                    old.setdefault(name, body)
                else:
                    new.setdefault(name, body)
            continue
        saw_pkg = True
        name, ver = _norm_pkg(match.group(1)), match.group(2)
        if raw.startswith("-"):
            old[name] = ver
        else:
            new[name] = ver
    return old, new, saw_hash, saw_pkg


def parse_action_ref_maps(patch: str) -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, str]]]:
    old: dict[str, tuple[str, str]] = {}
    new: dict[str, tuple[str, str]] = {}
    for raw in patch.splitlines():
        if raw.startswith("---") or raw.startswith("+++"):
            continue
        if not (raw.startswith("-") or raw.startswith("+")):
            continue
        match = USES_RE.search(raw)
        if not match:
            continue
        action = match.group("action")
        ref = match.group("ref")
        comment = raw.split("#", 1)[1] if "#" in raw else ""
        if raw.startswith("-"):
            old[action] = (ref, comment)
        else:
            new[action] = (ref, comment)
    return old, new


def snapshot_risk_from_files(files: Sequence[Mapping[str, Any]], kind_hint: str | None) -> dict[str, Any]:
    members: list[dict[str, Any]] = []
    for item in files:
        if not isinstance(item, dict):
            members.append({"risk": "review-required", "auto_eligible": False, "reason": "malformed-file-entry"})
            continue
        name = str(item.get("filename") or "")
        patch = str(item.get("patch") or "")
        if name == ".python-version":
            old = new = None
            for line in patch.splitlines():
                if line.startswith("-") and not line.startswith("---"):
                    try:
                        old = str(parse_version(line[1:].strip()))
                    except ValueError:
                        pass
                if line.startswith("+") and not line.startswith("+++"):
                    try:
                        new = str(parse_version(line[1:].strip()))
                    except ValueError:
                        pass
            if old and new:
                members.append(classify_python_change(old, new))
            else:
                members.append({"risk": "review-required", "auto_eligible": False, "reason": "pin-unparsed"})
        elif name in _REQ_FILES:
            if not patch:
                members.append({
                    "risk": "review-required", "auto_eligible": False,
                    "reason": "truncated-or-missing-patch", "name": name,
                })
                continue
            policy_members = requirement_policy_members(patch)
            members.extend(policy_members)
            hash_members = requirement_hash_members(patch)
            members.extend(hash_members)
            old_map, new_map, saw_hash, saw_pkg = parse_requirement_version_maps(patch)
            names = set(old_map) | set(new_map)
            if not names:
                if policy_members or hash_members:
                    continue
                reason = "hash-only" if saw_hash else (
                    "unparsed-requirement-diff" if saw_pkg else "truncated-or-missing-patch"
                )
                members.append({"risk": "review-required", "auto_eligible": False, "reason": reason, "name": name})
                continue
            for pkg in sorted(names):
                if pkg not in old_map or pkg not in new_map:
                    members.append({
                        "risk": "review-required", "auto_eligible": False,
                        "reason": "package-added-or-removed", "name": pkg,
                    })
                    continue
                members.append(classify_package_update(old_map[pkg], new_map[pkg], name=pkg))
        elif name.endswith((".yml", ".yaml")):
            if diff_touches_workflow_policy(patch):
                members.append({"risk": "review-required", "auto_eligible": False, "reason": "workflow-policy-change"})
                continue
            old_refs, new_refs = parse_action_ref_maps(patch)
            actions = set(old_refs) | set(new_refs)
            if not actions:
                reason = "truncated-or-missing-patch" if not patch else "workflow-unparsed"
                members.append({"risk": "review-required", "auto_eligible": False, "reason": reason, "name": name})
                continue
            for action in sorted(actions):
                if action not in old_refs or action not in new_refs:
                    members.append({
                        "risk": "review-required", "auto_eligible": False,
                        "reason": "new-or-moved-action", "name": action,
                    })
                    continue
                old_ref, old_c = old_refs[action]
                new_ref, new_c = new_refs[action]
                members.append(classify_action_update(
                    old_ref, new_ref, old_action=action, new_action=action,
                    comment_old=old_c, comment_new=new_c,
                ))
        else:
            members.append({"risk": "review-required", "auto_eligible": False, "reason": f"path:{name}"})
    if not members:
        return {"risk": "review-required", "auto_eligible": False, "reason": "empty-diff"}
    return highest_risk(members)


def merge_pull(owner: str, repo: str, number: int, sha: str, method: str, token: str, fallbacks: Sequence[str]) -> Decision:
    methods = [method, *[m for m in fallbacks if m != method]]
    last_message = "merge-failed"
    for current in methods:
        status, payload = _github_json(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/merge",
            token,
            method="PUT",
            body={"sha": sha, "merge_method": current},
        )
        if status in (200, 201) and isinstance(payload, dict) and payload.get("merged") is True:
            return Decision("merged", "merged", risk="routine", merge_method=current)
        if status == 405 and isinstance(payload, dict):
            message = str(payload.get("message") or "")
            last_message = message or "method-not-allowed"
            if "not allowed" in message.lower() or "merge method" in message.lower():
                continue
            return Decision("fail", f"merge-http-405:{message}", risk="blocked")
        if status in {0, 502, 503, 504}:
            return Decision("fail", f"merge-api-error:{status}", risk="blocked")
        if isinstance(payload, dict) and payload.get("merged") is False:
            return Decision("fail", f"merge-declined:{payload.get('message')}", risk="blocked")
        last_message = f"merge-http-{status}"
        break
    return Decision("fail", last_message, risk="blocked")


def cmd_apply_live(args: argparse.Namespace) -> int:
    """Trusted-base live adapter. Explicit opt-in; never used by fixture tests."""
    token = os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        print("GITHUB_TOKEN missing", file=sys.stderr)
        return 2
    event_path = os.environ.get("GITHUB_EVENT_PATH") or ""
    if not event_path or not Path(event_path).is_file():
        print("GITHUB_EVENT_PATH missing", file=sys.stderr)
        return 2
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    profile = load_profile(args.profile)
    built = build_live_snapshot(event, token, profile)
    if isinstance(built, Decision):
        json.dump(built.to_json(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0 if built.action in {"defer", "review-required"} else 1
    decision = decide_merge(built)
    if decision.action == "merge" and args.apply_live:
        refreshed = build_live_snapshot(event, token, profile)
        if isinstance(refreshed, Decision):
            decision = refreshed
        elif str(refreshed.get("head_sha") or "") != str(built.get("head_sha") or ""):
            decision = Decision("fail", "head-changed", risk="blocked")
        else:
            decision = decide_merge(refreshed)
            if decision.action == "merge":
                built = refreshed
    if decision.action == "merge" and args.apply_live:
        repo = str(built["repository"])
        owner, name = repo.split("/", 1)
        number = int(built["pull_request"]["number"])
        fallbacks = list(profile.get("fallback_merge_methods") or ["merge"])
        decision = merge_pull(
            owner, name, number, str(built["head_sha"]),
            str(decision.merge_method or "squash"), token, fallbacks,
        )
        # Re-read to confirm rather than trusting a false merged flag.
        if decision.action == "merged":
            status, pr = _github_json(f"https://api.github.com/repos/{owner}/{name}/pulls/{number}", token)
            if status != 200 or not isinstance(pr, dict) or pr.get("merged") is not True:
                decision = Decision("fail", "merge-unconfirmed", risk="blocked")
    json.dump(decision.to_json(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if decision.action in {"merge", "merged", "defer", "review-required"} else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="News-Express / Game-Express maintenance policy")
    sub = parser.add_subparsers(dest="cmd", required=True)
    decide = sub.add_parser("decide", help="side-effect-free merge decision")
    decide.add_argument("--fixture", required=True)
    decide.add_argument("--apply", action="store_true")
    decide.set_defaults(func=cmd_decide)
    select = sub.add_parser("select", help="python candidate selection from a fixture")
    select.add_argument("--fixture", required=True)
    select.set_defaults(func=cmd_select)
    checks = sub.add_parser("classify-checks", help="classify check runs from a fixture")
    checks.add_argument("--fixture", required=True)
    checks.set_defaults(func=cmd_classify_checks)
    apply_live = sub.add_parser("apply-live", help="explicit live merge adapter (trusted base only)")
    apply_live.add_argument("--profile", default=str(DEFAULT_PROFILE))
    apply_live.add_argument("--apply-live", action="store_true")
    apply_live.set_defaults(func=cmd_apply_live)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
