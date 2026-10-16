#!/usr/bin/env python3
"""Portable maintenance helpers shared across News-family proposal heads.

This module is the News-local common-helper *candidate*. It is not approved
for blind adoption and does not prove Game / Reddit / Twitter compatibility.
Engines, layouts, and production state stay out of this layer.

Callers inject GitHub HTTP (``get_json`` / ``get_pages``). Decision functions
are pure: missing evidence fails closed and never invents a clean scan,
producer, or publication.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

SCHEMA_VERSION = 1

# Pinned compiler. Merge controller and lock-consistency must not drift about
# which pip / pip-tools produced a validated lock graph.
PINNED_PIP = "26.1.1"
PINNED_PIP_TOOLS = "7.5.3"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

JsonGetter = Callable[[str], tuple[int, Any]]
PagesGetter = Callable[[str], tuple[int, Any]]

# --- Repository association -------------------------------------------------

def repo_association_failure(pr: Mapping[str, Any], expected_repo: str) -> str:
    """Bind both sides of a PR to the trusted policy repository.

    Branch name and base ref alone are not provenance. A fork head or a
    missing association must never reach the merge call.
    """
    if not expected_repo:
        return "missing-expected-repository"
    head = pr.get("head") if isinstance(pr.get("head"), dict) else {}
    base = pr.get("base") if isinstance(pr.get("base"), dict) else {}
    head_repo = head.get("repo") if isinstance(head.get("repo"), dict) else {}
    base_repo = base.get("repo") if isinstance(base.get("repo"), dict) else {}
    head_full = str(head_repo.get("full_name") or "")
    base_full = str(base_repo.get("full_name") or "")
    if not head_full or not base_full:
        return "missing-repo-association"
    if base_full != expected_repo:
        return "foreign-base-repository"
    if head_full != expected_repo:
        return "cross-fork-head"
    return ""


# --- Producer identity ------------------------------------------------------
#
# A check name plus a github-actions app slug is not identity: anything able
# to create a check run can choose a familiar name. Each mandatory gate is
# bound to the workflow file and job approved to produce it, resolved from
# the check's own run and job identifiers. Unresolved, unavailable, or
# mismatched evidence blocks; nothing is inferred from the name.

_CHECK_RUN_URL_RE = re.compile(
    r"^https://github\.com/([^/\s]+)/([^/\s]+)/actions/runs/(\d+)/job/(\d+)/?$"
)
_CHECK_RUN_API_RE = re.compile(
    r"^https://api\.github\.com/repos/([^/\s]+)/([^/\s]+)/check-runs/(\d+)/?$"
)


def parse_check_run_identity(details_url: Any, expected_repository: str) -> tuple[int, int] | None:
    """Return (run_id, job_id) only for a run belonging to the expected repository."""
    match = _CHECK_RUN_URL_RE.match(str(details_url or "").strip())
    if not match:
        return None
    owner, repo, run_id, job_id = match.groups()
    if f"{owner}/{repo}" != str(expected_repository or ""):
        return None
    return int(run_id), int(job_id)


def _as_positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def collect_producer_evidence(
    owner: str,
    name: str,
    check_runs: Sequence[Mapping[str, Any]],
    expected_names: Sequence[str],
    get_json: JsonGetter,
) -> dict[str, Any]:
    """Resolve each mandatory check to the workflow run and job that produced it.

    ``get_json(url) -> (status, payload)`` is injected so this module never
    owns a token or a network client.
    """
    expected = {n for n in expected_names if n}
    evidence: dict[str, Any] = {}
    for run in check_runs or []:
        if not isinstance(run, dict):
            continue
        check_name = str(run.get("name") or "")
        if check_name not in expected or check_name in evidence:
            continue
        identity = parse_check_run_identity(
            run.get("details_url") or run.get("html_url"), f"{owner}/{name}"
        )
        if identity is None:
            evidence[check_name] = {"error": "unresolvable-details-url"}
            continue
        run_id, job_id = identity
        status, job = get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/jobs/{job_id}"
        )
        if status != 200 or not isinstance(job, dict):
            evidence[check_name] = {"error": f"job-api:{status}"}
            continue
        status, wf_run = get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/runs/{run_id}"
        )
        if status != 200 or not isinstance(wf_run, dict):
            evidence[check_name] = {"error": f"run-api:{status}"}
            continue
        evidence[check_name] = {
            "workflow": str(wf_run.get("path") or ""),
            "job": str(job.get("name") or ""),
            "check_run_id": _as_positive_int(run.get("id")),
            "run_id": run_id,
            "run_record_id": _as_positive_int(wf_run.get("id")),
            "job_id": job_id,
            "job_record_id": _as_positive_int(job.get("id")),
            "job_run_id": _as_positive_int(job.get("run_id")),
            "job_check_run_url": str(job.get("check_run_url") or ""),
            "run_attempt": _as_positive_int(wf_run.get("run_attempt")),
            "job_run_attempt": _as_positive_int(job.get("run_attempt")),
            "head_sha": str(wf_run.get("head_sha") or ""),
            "job_head_sha": str(job.get("head_sha") or ""),
            "job_status": str(job.get("status") or ""),
            "job_conclusion": str(job.get("conclusion") or ""),
            "run_status": str(wf_run.get("status") or ""),
            "run_conclusion": str(wf_run.get("conclusion") or ""),
        }
    return evidence


def verify_check_producers(
    evidence: Mapping[str, Any] | None,
    *,
    expected_names: Sequence[str],
    head_sha: str,
    producers: Mapping[str, Any] | None,
    repository: str = "",
) -> dict[str, Any]:
    """Pure producer binding. Every gap blocks; nothing is inferred from a name.

    Matching workflow, job, and head are not enough. The job has to be the one
    the check run pointed at, it has to belong to the run that was fetched,
    both have to describe the same attempt, and both have to have completed
    successfully. A separately green same-named check does not compensate.
    """
    if not producers:
        return {"state": "failed", "reason": "no-approved-producers-configured"}
    if not SHA_RE.fullmatch((head_sha or "").lower()):
        return {"state": "failed", "reason": "missing-head-sha"}
    for check_name in expected_names:
        approved = producers.get(check_name)
        if not isinstance(approved, dict):
            return {"state": "failed", "reason": f"no-approved-producer:{check_name}"}
        found = (evidence or {}).get(check_name)
        if not isinstance(found, dict):
            return {"state": "failed", "reason": f"missing-producer-evidence:{check_name}"}
        if found.get("error"):
            return {
                "state": "failed",
                "reason": f"producer-evidence-unavailable:{check_name}:{found['error']}",
            }
        failure = _producer_identity_failure(check_name, found) or _producer_check_link_failure(
            check_name, found, repository
        )
        if failure:
            return {"state": "failed", "reason": failure}
        if str(found.get("workflow") or "") != str(approved.get("workflow") or ""):
            return {"state": "failed", "reason": f"unapproved-producer-workflow:{check_name}"}
        if str(found.get("job") or "") != str(approved.get("job") or ""):
            return {"state": "failed", "reason": f"unapproved-producer-job:{check_name}"}
        if str(found.get("head_sha") or "") != str(head_sha):
            return {"state": "failed", "reason": f"producer-head-mismatch:{check_name}"}
        if str(found.get("job_head_sha") or "") != str(head_sha):
            return {"state": "failed", "reason": f"producer-job-head-mismatch:{check_name}"}
        outcome = _producer_outcome_failure(check_name, found)
        if outcome:
            return {"state": "failed", "reason": outcome}
    return {"state": "ready", "reason": "producers-verified"}


def _producer_identity_failure(check_name: str, found: Mapping[str, Any]) -> str:
    run_id = found.get("run_id")
    job_id = found.get("job_id")
    if not isinstance(run_id, int) or run_id <= 0:
        return f"producer-missing-run-id:{check_name}"
    if not isinstance(job_id, int) or job_id <= 0:
        return f"producer-missing-job-id:{check_name}"
    if found.get("job_record_id") != job_id:
        return f"producer-job-id-mismatch:{check_name}"
    if found.get("job_run_id") != run_id:
        return f"producer-run-id-mismatch:{check_name}"
    if found.get("run_record_id") != run_id:
        return f"producer-run-record-mismatch:{check_name}"
    run_attempt = found.get("run_attempt")
    if not isinstance(run_attempt, int) or run_attempt <= 0:
        return f"producer-missing-run-attempt:{check_name}"
    if found.get("job_run_attempt") != run_attempt:
        return f"producer-attempt-mismatch:{check_name}"
    return ""


def _producer_check_link_failure(
    check_name: str, found: Mapping[str, Any], repository: str
) -> str:
    """Bind the fetched job to the exact check run being authenticated."""
    check_run_id = found.get("check_run_id")
    if not isinstance(check_run_id, int) or check_run_id <= 0:
        return f"producer-missing-check-run-id:{check_name}"
    url = str(found.get("job_check_run_url") or "").strip()
    match = _CHECK_RUN_API_RE.match(url)
    if not match:
        return f"producer-missing-check-run-url:{check_name}"
    owner, repo, linked_id = match.groups()
    if repository and f"{owner}/{repo}" != repository:
        return f"producer-check-run-foreign-repository:{check_name}"
    if int(linked_id) != check_run_id:
        return f"producer-check-run-id-mismatch:{check_name}"
    return ""


def _producer_outcome_failure(check_name: str, found: Mapping[str, Any]) -> str:
    if str(found.get("job_status") or "") != "completed":
        return f"producer-job-not-completed:{check_name}:{found.get('job_status') or 'unknown'}"
    if str(found.get("job_conclusion") or "") != "success":
        return f"producer-job-not-successful:{check_name}:{found.get('job_conclusion') or 'unknown'}"
    if str(found.get("run_status") or "") != "completed":
        return f"producer-run-not-completed:{check_name}:{found.get('run_status') or 'unknown'}"
    if str(found.get("run_conclusion") or "") != "success":
        return f"producer-run-not-successful:{check_name}:{found.get('run_conclusion') or 'unknown'}"
    return ""


# --- Security evidence ------------------------------------------------------
#
# code-scanning/analyses describes scan *executions* and carries results_count;
# it has no open/resolved state. Only code-scanning/alerts describes findings.
# Counting an alert-only field on an analysis record silently yields zero, so
# analyses prove a scan completed on this head, and alerts establish findings.

_CODE_SCAN_ANALYSES = "code-scanning/analyses"
_CODE_SCAN_ALERTS = "code-scanning/alerts"
_SECRET_SCAN_ALERTS = "secret-scanning/alerts"
_CODE_SCAN_ALERT_STATES = {"open", "dismissed", "fixed", "resolved"}
_SECRET_ALERT_STATES = {"open", "resolved"}


def security_policy(source: Mapping[str, Any] | None) -> tuple[str, list[str]]:
    """Resolve the security-evidence policy as (mode, required kinds).

    A repository either requires named scan evidence or has deliberately
    declared that it requires none. Those are different statements, and only
    the second one is allowed to skip the gate.
    """
    source = source if isinstance(source, Mapping) else {}
    block = source.get("security_evidence")
    if isinstance(block, dict):
        mode = str(block.get("mode") or "")
        kinds = [str(k) for k in (block.get("required") or []) if k]
    else:
        mode = str(source.get("security_evidence_mode") or "")
        kinds = [str(k) for k in (source.get("required_security_evidence") or []) if k]
    if kinds:
        return "required", kinds
    return ("disabled" if mode == "disabled" else "unconfigured"), []


def collect_security_evidence(
    owner: str,
    name: str,
    head_sha: str,
    required: Sequence[str],
    get_pages: PagesGetter,
    ref: str = "",
) -> dict[str, Any]:
    """Retrieve actual scan completion and findings for the required kinds."""
    out: dict[str, Any] = {}
    for kind in required or []:
        key = str(kind)
        if key == "code-scanning":
            out[key] = _collect_code_scanning(owner, name, head_sha, get_pages, ref)
        elif key == "secret-scanning":
            out[key] = _collect_alerts(owner, name, _SECRET_SCAN_ALERTS, get_pages, key)
        else:
            out[key] = {"state": "unknown-kind"}
    return out


def _collect_code_scanning(
    owner: str,
    name: str,
    head_sha: str,
    get_pages: PagesGetter,
    ref: str = "",
) -> dict[str, Any]:
    base = f"https://api.github.com/repos/{owner}/{name}"
    status, analyses = get_pages(
        f"{base}/{_CODE_SCAN_ANALYSES}?commit_sha={head_sha}&per_page=100&page=1"
    )
    if status != 200:
        return {"state": "unavailable", "detail": f"analyses-http:{status}"}
    if not isinstance(analyses, list):
        return {"state": "malformed"}
    current = [
        item
        for item in analyses
        if isinstance(item, dict) and str(item.get("commit_sha") or "") == head_sha
    ]
    if not current:
        return {"state": "no-analysis-for-head"}
    errored = [
        item for item in current if isinstance(item, dict) and item.get("error") not in (None, "")
    ]
    if errored:
        return {"state": "analysis-error", "count": len(errored)}
    scope = str(ref or "").strip()
    if not scope:
        return {"state": "missing-ref-scope", "analyses": len(current)}
    result = _collect_alerts(
        owner, name, _CODE_SCAN_ALERTS, get_pages, "code-scanning", ref=scope
    )
    if result.get("state") != "ok":
        return result
    result["analyses"] = len(current)
    result["ref"] = scope
    return result


def _collect_alerts(
    owner: str,
    name: str,
    endpoint: str,
    get_pages: PagesGetter,
    key: str,
    ref: str = "",
) -> dict[str, Any]:
    base = f"https://api.github.com/repos/{owner}/{name}"
    query = "?state=open&per_page=100&page=1"
    if ref:
        query += f"&ref={urllib.parse.quote(ref, safe='')}"
    status, alerts = get_pages(f"{base}/{endpoint}{query}")
    if status != 200:
        return {"state": "unavailable", "detail": f"alerts-http:{status}"}
    if not isinstance(alerts, list):
        return {"state": "malformed"}
    open_count = _count_open_alerts(alerts, code_scanning=key == "code-scanning")
    if open_count is None:
        return {"state": "malformed"}
    return {"state": "ok", "open": open_count}


def _count_open_alerts(alerts: Sequence[Any], *, code_scanning: bool) -> int | None:
    """Count open alerts, or return None if the payload is not alert-shaped."""
    total = 0
    for item in alerts:
        if not isinstance(item, dict):
            return None
        top = item.get("state")
        if not isinstance(top, str) or not top:
            return None
        if code_scanning:
            if top not in _CODE_SCAN_ALERT_STATES:
                return None
            instance = item.get("most_recent_instance")
            if not isinstance(instance, dict):
                return None
            inner = instance.get("state")
            if not isinstance(inner, str) or inner not in _CODE_SCAN_ALERT_STATES:
                return None
            if (top == "open") != (inner == "open"):
                return None
            if inner == "open":
                total += 1
        else:
            if top not in _SECRET_ALERT_STATES:
                return None
            if top == "open":
                total += 1
    return total


def verify_security_evidence(
    evidence: Mapping[str, Any] | None,
    required: Sequence[str],
    *,
    mode: str = "",
) -> dict[str, Any]:
    """Open findings block; unavailable evidence defers. Neither reads as clean.

    An empty requirement list is not a pass. It is either a documented
    decision that this repository requires no scan evidence, or a
    configuration gap, and the two are reported differently.
    """
    kinds = [str(kind) for kind in (required or []) if kind]
    if not kinds:
        if str(mode) == "disabled":
            return {"state": "ready", "reason": "security-evidence-not-required"}
        return {"state": "failed", "reason": "security-evidence-unconfigured"}
    for key in kinds:
        found = (evidence or {}).get(key)
        if not isinstance(found, dict):
            return {"state": "defer", "reason": f"security-evidence-missing:{key}"}
        state = str(found.get("state") or "")
        if state == "ok":
            try:
                open_count = int(found.get("open") or 0)
            except (TypeError, ValueError):
                return {"state": "defer", "reason": f"security-evidence-unavailable:{key}:malformed-open"}
            if open_count > 0:
                return {"state": "failed", "reason": f"unresolved-{key}-alerts:{open_count}"}
            continue
        return {"state": "defer", "reason": f"security-evidence-unavailable:{key}:{state}"}
    return {"state": "ready", "reason": "security-evidence-satisfied"}


# --- Candidate publication provenance ---------------------------------------

DEFAULT_PROPOSER_PATH = ".github/workflows/python_version_bump.yml"
DEFAULT_PROPOSAL_FILES = (
    ".python-version",
    "requirements.txt",
    "requirements-dev.txt",
    ".github/maintenance.json",
)


def publication_policy(source: Mapping[str, Any] | None) -> tuple[str, str, tuple[str, ...]]:
    """Resolve (mode, trusted proposer path, proposal files)."""
    source = source if isinstance(source, Mapping) else {}
    block = source.get("publication_evidence")
    if isinstance(block, dict):
        mode = str(block.get("mode") or "")
        path = str(block.get("proposer_workflow") or DEFAULT_PROPOSER_PATH)
        files = tuple(str(f) for f in (block.get("proposal_files") or DEFAULT_PROPOSAL_FILES) if f)
        return (mode or "unconfigured"), path, files
    mode = str(source.get("publication_evidence_mode") or "")
    return (mode or "unconfigured"), DEFAULT_PROPOSER_PATH, DEFAULT_PROPOSAL_FILES


def verify_publication_gate(
    *,
    mode: str,
    kind: str,
    evidence: Mapping[str, Any] | None,
    pr: Mapping[str, Any],
    candidate_version: str | None = None,
    trusted_proposer_path: str = DEFAULT_PROPOSER_PATH,
    proposal_files: Sequence[str] = DEFAULT_PROPOSAL_FILES,
    pinned_pip: str = PINNED_PIP,
    pinned_pip_tools: str = PINNED_PIP_TOOLS,
    repository: str = "",
) -> dict[str, Any]:
    """Profile-gated publication binding.

    Dependabot PRs do not emit proposer records. Python-bump PRs require an
    explicit mode: ``disabled`` is a recorded decision; an omitted mode is a
    configuration gap, not a pass.
    """
    if kind != "python_bump":
        return {"state": "ready", "reason": "publication-not-applicable"}
    if str(mode) == "disabled":
        return {"state": "ready", "reason": "publication-evidence-not-required"}
    if str(mode) != "required":
        return {"state": "failed", "reason": "publication-evidence-unconfigured"}
    return verify_publication_record(
        evidence or {},
        pr,
        candidate_version=candidate_version,
        trusted_proposer_path=trusted_proposer_path,
        proposal_files=proposal_files,
        pinned_pip=pinned_pip,
        pinned_pip_tools=pinned_pip_tools,
        repository=repository,
    )


def verify_publication_record(
    evidence: Mapping[str, Any],
    pr: Mapping[str, Any],
    *,
    candidate_version: str | None,
    trusted_proposer_path: str,
    proposal_files: Sequence[str],
    pinned_pip: str,
    pinned_pip_tools: str,
    repository: str,
) -> dict[str, Any]:
    """Bind a published proposal to the run and attempt that validated it.

    A branch name, a title, or a time window identifies nothing. Three
    identities stay distinct: the run actor, the PAT publisher, and the
    configured commit bot. Digests compared here are supplied by the caller
    from published file contents, so a proposal cannot vouch for itself.
    """
    if not isinstance(evidence, Mapping):
        return {"state": "failed", "reason": "publication-evidence-unavailable"}
    repo = str(evidence.get("repository") or repository or "").strip()
    if not repo:
        return {"state": "failed", "reason": "publication-evidence-no-repository"}

    run = evidence.get("proposer_run")
    if not isinstance(run, dict) or not run:
        return {"state": "failed", "reason": "no-proposer-run"}
    if str(run.get("path") or "") != trusted_proposer_path:
        return {"state": "failed", "reason": "untrusted-proposer-workflow"}
    if not isinstance(run.get("id"), int) or run["id"] <= 0:
        return {"state": "failed", "reason": "proposer-run-missing-id"}
    if not isinstance(run.get("workflow_id"), int) or run["workflow_id"] <= 0:
        return {"state": "failed", "reason": "proposer-run-missing-workflow-id"}
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        return {"state": "failed", "reason": "proposer-run-not-success"}
    for key in ("repository", "head_repository"):
        record = run.get(key)
        full_name = record.get("full_name") if isinstance(record, dict) else record
        if full_name != repo:
            return {"state": "failed", "reason": f"proposer-run-foreign-{key}"}
    if not isinstance(run.get("run_attempt"), int) or run["run_attempt"] <= 0:
        return {"state": "failed", "reason": "proposer-run-missing-attempt"}

    attempt = evidence.get("proposer_attempt")
    if not isinstance(attempt, dict) or not attempt:
        return {"state": "failed", "reason": "proposer-attempt-unavailable"}
    if attempt.get("id") != run["id"] or attempt.get("run_attempt") != run["run_attempt"]:
        return {"state": "failed", "reason": "proposer-attempt-mismatch"}
    if attempt.get("status") != "completed" or attempt.get("conclusion") != "success":
        return {"state": "failed", "reason": "proposer-attempt-not-success"}
    if attempt.get("head_sha") != run.get("head_sha"):
        return {"state": "failed", "reason": "proposer-attempt-head-mismatch"}

    validation = evidence.get("validation_record")
    publication = evidence.get("publication_record")
    if not isinstance(validation, dict) or not validation:
        return {"state": "failed", "reason": "missing-validation-record"}
    if not isinstance(publication, dict) or not publication:
        return {"state": "failed", "reason": "missing-publication-record"}
    for label, record in (("validation", validation), ("publication", publication)):
        if record.get("run_id") != run["id"] or record.get("run_attempt") != run["run_attempt"]:
            return {"state": "failed", "reason": f"{label}-record-run-mismatch"}

    head = str((pr.get("head") or {}).get("sha") or "")
    branch = str((pr.get("head") or {}).get("ref") or "")
    number = pr.get("number")
    if not head:
        return {"state": "failed", "reason": "proposal-head-unavailable"}
    if publication.get("pull_number") != number:
        return {"state": "failed", "reason": "publication-pr-mismatch"}
    if publication.get("published_head") != head:
        return {"state": "failed", "reason": "publication-head-mismatch"}
    if branch and publication.get("branch") != branch:
        return {"state": "failed", "reason": "publication-branch-mismatch"}

    actual_author = ((pr.get("user") or {}).get("login")) or None
    if not publication.get("pr_author"):
        return {"state": "failed", "reason": "publication-missing-pr-author"}
    if actual_author and publication["pr_author"] != actual_author:
        return {"state": "failed", "reason": "publication-pr-author-mismatch"}
    actor = ((run.get("actor") or {}).get("login")) or None
    if not publication.get("run_actor"):
        return {"state": "failed", "reason": "publication-missing-run-actor"}
    if actor and publication["run_actor"] != actor:
        return {"state": "failed", "reason": "publication-run-actor-mismatch"}
    expected_commit = evidence.get("expected_commit_identity")
    if not publication.get("commit_identity"):
        return {"state": "failed", "reason": "publication-missing-commit-identity"}
    if expected_commit and publication["commit_identity"] != expected_commit:
        return {"state": "failed", "reason": "publication-commit-identity-mismatch"}

    if not validation.get("source_head"):
        return {"state": "failed", "reason": "validation-missing-source-head"}
    if validation["source_head"] != run.get("head_sha"):
        return {"state": "failed", "reason": "validation-source-head-mismatch"}
    if not candidate_version:
        return {"state": "failed", "reason": "candidate-version-unparsed"}
    if validation.get("candidate_version") != candidate_version:
        return {"state": "failed", "reason": "validation-candidate-mismatch"}
    if validation.get("interpreter") != candidate_version:
        return {"state": "failed", "reason": "validation-interpreter-mismatch"}
    if validation.get("pip") != pinned_pip or validation.get("pip_tools") != pinned_pip_tools:
        return {"state": "failed", "reason": "validation-compiler-mismatch"}

    recorded = validation.get("digests")
    actual = evidence.get("proposal_digests")
    if not isinstance(recorded, dict) or not recorded:
        return {"state": "failed", "reason": "validation-missing-digests"}
    if not isinstance(actual, dict) or not actual:
        return {"state": "failed", "reason": "proposal-digests-uncomputed"}
    published = publication.get("digests")
    if not isinstance(published, dict) or not published:
        return {"state": "failed", "reason": "publication-missing-digests"}
    for name in proposal_files:
        if name not in recorded:
            return {"state": "failed", "reason": f"validation-missing-digest:{name}"}
        if recorded[name] != actual.get(name):
            return {"state": "failed", "reason": f"validation-digest-mismatch:{name}"}
        if published.get(name) != actual.get(name):
            return {"state": "failed", "reason": f"publication-digest-mismatch:{name}"}

    commit = evidence.get("published_commit")
    if not isinstance(commit, dict) or commit.get("sha") != head:
        return {"state": "failed", "reason": "published-head-not-a-commit"}
    return {"state": "ready", "reason": "publication-verified"}


# --- python.org release-age authority ---------------------------------------
#
# setup-python versions-manifest timestamps record archive publication, not
# the CPython release. A rebuilt archive must not redefine soak age. Unknown
# age never becomes "up to date".

RELEASE_DATE_API = "https://www.python.org/api/v2/downloads/release/"
RELEASE_DATE_MAX_PAGES = 3
RELEASE_DATE_TIMEOUT = 10
RELEASE_DATE_CACHE_TTL_SECONDS = 86400
_RELEASE_NAME_RE = re.compile(r"^Python\s+(\d+\.\d+\.\d+)\s*$")
RELEASE_DATE_SOURCE = "python.org-downloads-api"


def _default_release_date_cache() -> Path:
    override = os.environ.get("PYTHON_RELEASE_DATE_CACHE")
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "python-release-dates.json"


def parse_iso_date(value: str | None) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _read_release_date_cache(path: Path, now: datetime) -> dict[str, str] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    fetched = parse_iso_date(str(raw.get("fetched_at") or ""))
    dates = raw.get("dates")
    if fetched is None or not isinstance(dates, dict):
        return None
    if (now - fetched).total_seconds() > RELEASE_DATE_CACHE_TTL_SECONDS:
        return None
    return {str(k): str(v) for k, v in dates.items() if isinstance(v, str)}


def fetch_release_dates(
    *,
    opener: Any | None = None,
    max_pages: int = RELEASE_DATE_MAX_PAGES,
    timeout: int = RELEASE_DATE_TIMEOUT,
    cache_path: Path | None = None,
    now: datetime | None = None,
) -> tuple[dict[str, str], str, str]:
    """Return (version -> ISO date, state, detail) from python.org.

    state is ``cache`` or ``ok`` when dates were obtained, and ``unavailable``
    when the authority could not be reached or returned nothing usable.
    """
    now = now or datetime.now(timezone.utc)
    cache_path = cache_path or _default_release_date_cache()
    cached = _read_release_date_cache(cache_path, now)
    if cached:
        return cached, "cache", str(cache_path)

    request = opener or urllib.request.urlopen
    dates: dict[str, str] = {}
    last_error = "no-records"
    for page in range(1, max(1, int(max_pages)) + 1):
        url = f"{RELEASE_DATE_API}?is_published=true&page={page}&page_size=100"
        try:
            with request(url, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # network, timeout, JSON or HTTP error
            if not dates:
                return {}, "unavailable", f"{type(exc).__name__}: {exc}"
            break
        records = payload.get("results") if isinstance(payload, dict) else payload
        if not isinstance(records, list) or not records:
            break
        for record in records:
            if not isinstance(record, dict):
                continue
            match = _RELEASE_NAME_RE.match(str(record.get("name") or "").strip())
            if not match:
                continue
            parsed = parse_iso_date(str(record.get("release_date") or ""))
            if parsed is None:
                continue
            dates.setdefault(match.group(1), parsed.date().isoformat())
        last_error = ""
        if not (isinstance(payload, dict) and payload.get("next")):
            break
    if not dates:
        return {}, "unavailable", last_error or "no-parseable-records"
    try:
        cache_path.write_text(
            json.dumps({"fetched_at": now.isoformat(), "dates": dates}, sort_keys=True),
            encoding="utf-8",
        )
    except OSError:
        pass
    return dates, "ok", f"{len(dates)} releases"


def apply_release_dates(
    manifest: Sequence[Mapping[str, Any]],
    dates: Mapping[str, str],
    state: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Attach python.org dates. Setup-python timestamps are not soak age.

    A rebuilt archive's ``published_at`` must not silently redefine age.
    Unknown versions stay without a date so the selector defers.
    """
    enriched: list[dict[str, Any]] = []
    resolved: list[str] = []
    unknown: list[str] = []
    stripped: list[str] = []
    for entry in manifest:
        if not isinstance(entry, dict):
            continue
        item = dict(entry)
        version = str(item.get("version") or "").strip()
        trusted = str(item.get("release_date_source") or "") == RELEASE_DATE_SOURCE
        if not trusted:
            if item.get("published_at") or item.get("release_date"):
                if version:
                    stripped.append(version)
            item.pop("published_at", None)
            item.pop("release_date", None)
        authoritative = dates.get(version)
        if authoritative:
            item["release_date"] = authoritative
            item["release_date_source"] = RELEASE_DATE_SOURCE
            resolved.append(version)
        elif version:
            unknown.append(version)
        enriched.append(item)
    return enriched, {
        "authority": "python.org downloads API v2",
        "state": state,
        "resolved": sorted(set(resolved)),
        "unknown": sorted(set(unknown)),
        "stripped_untrusted_dates": sorted(set(stripped)),
    }


def compiler_pins(source: Mapping[str, Any] | None) -> tuple[str, str]:
    """Return (pip, pip-tools) from profile, falling back to the module pins."""
    source = source if isinstance(source, Mapping) else {}
    block = source.get("compiler") if isinstance(source.get("compiler"), dict) else {}
    pip = str(block.get("pip") or PINNED_PIP)
    tools = str(block.get("pip_tools") or PINNED_PIP_TOOLS)
    return pip, tools
