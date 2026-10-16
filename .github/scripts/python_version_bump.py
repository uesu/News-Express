#!/usr/bin/env python3
"""Thin runtime-proposer adapter.

Selection, soak, and risk policy live in maintenance.py. This entry point
reads `.python-version`, optionally a fixture, and prints a JSON result.
It never merges, never rewrites README/history, and treats missing optional
docs as success for production copies.

Release-age authority is python.org (maintenance_common.fetch_release_dates).
The setup-python versions-manifest ``published_at`` is archive publication,
not the CPython release date, and is not used for soak.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import maintenance  # noqa: E402
import maintenance_common  # noqa: E402

REPO_ROOT = maintenance.REPO_ROOT


def rewrite_pin(path: Path, new_version: str) -> None:
    path.write_text(f"{new_version}\n", encoding="utf-8")


def optional_docs_present(profile: dict, root: Path) -> bool:
    docs = profile.get("optional_docs") or []
    return all((root / rel).exists() for rel in docs)


def _positive_int(value: str) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _distribution_version(dist_name: str) -> str:
    """Installed distribution version. Package ``__version__`` is not authority.

    pip-tools 7.5.3 does not expose ``piptools.__version__``. Profile pin
    strings are not a measurement of the environment.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:
        return ""
    try:
        found = version(dist_name)
    except PackageNotFoundError:
        return ""
    except Exception:
        return ""
    return str(found or "")


def _toolchain_versions() -> tuple[str, str, str]:
    interpreter = ".".join(str(part) for part in sys.version_info[:3])
    return interpreter, _distribution_version("pip"), _distribution_version("pip-tools")


def fetch_manifest_release_date(entry: dict) -> str | None:
    """Documented non-authority. Do not use this for soak age.

    The GitHub release ``published_at`` for ``actions/python-versions`` is the
    **setup-python artifact publication time**, not the CPython python.org
    release date. Kept so callers that still probe the archive timestamp can
    see it is not the soak authority.
    """
    for key in ("release_date", "published_at"):
        raw = str(entry.get(key) or "")
        if maintenance.parse_iso_date(raw):
            return raw
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", help="side-effect-free JSON fixture")
    parser.add_argument("--manifest", help="setup-python versions-manifest.json")
    parser.add_argument(
        "--release-date-cache",
        default="",
        help="cache file for authoritative upstream release dates",
    )
    parser.add_argument("--force", default="")
    parser.add_argument("--soak-days", type=int, default=0)
    parser.add_argument("--ignore-soak", action="store_true")
    parser.add_argument("--profile", default=str(maintenance.DEFAULT_PROFILE))
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--write-pin", action="store_true", help="rewrite .python-version only")
    parser.add_argument("--candidate", default="", help="with --write-pin, the version to write")
    parser.add_argument("--emit-validation", action="store_true", help="print a bound validation notice")
    parser.add_argument("--emit-publication", action="store_true", help="print a bound publication notice")
    parser.add_argument("--source-head", default="", help="validation source head SHA")
    parser.add_argument("--run-id", default="", help="workflow run id")
    parser.add_argument("--run-attempt", default="", help="workflow run attempt")
    parser.add_argument("--pull-number", default="", help="published PR number")
    parser.add_argument("--published-head", default="", help="published PR head SHA")
    parser.add_argument("--branch", default="", help="published branch")
    parser.add_argument("--pr-author", default="", help="PAT publisher login")
    parser.add_argument("--commit-identity", default="", help="configured commit bot login")
    parser.add_argument("--run-actor", default="", help="workflow run actor login")
    parser.add_argument("--interpreter", default="", help="override reported interpreter")
    parser.add_argument("--pip", default="", help="override reported pip version")
    parser.add_argument("--pip-tools", default="", help="override reported pip-tools version")
    args = parser.parse_args(argv)

    profile = maintenance.load_profile(args.profile)
    root = Path(args.root)
    pin_rel = str(profile.get("python", {}).get("pin_file") or ".python-version")
    pin_path = root / pin_rel

    pub_block = profile.get("publication_evidence") if isinstance(profile.get("publication_evidence"), dict) else {}
    proposal_files = [str(f) for f in (pub_block.get("proposal_files") or []) if f]
    if not proposal_files:
        proposal_files = list(maintenance_common.DEFAULT_PROPOSAL_FILES)

    if args.emit_validation or args.emit_publication:
        candidate = args.candidate or ""
        try:
            maintenance.parse_version(candidate)
        except ValueError:
            print("emit requires a valid --candidate", file=sys.stderr)
            return 2
        run_id = _positive_int(args.run_id or os.environ.get("GITHUB_RUN_ID") or "")
        run_attempt = _positive_int(args.run_attempt or os.environ.get("GITHUB_RUN_ATTEMPT") or "")
        digests = maintenance_common.digest_files(root, proposal_files)
        if args.emit_validation:
            source_head = (args.source_head or os.environ.get("GITHUB_SHA") or "").strip().lower()
            if not maintenance_common.SHA_RE.fullmatch(source_head):
                print("emit-validation requires --source-head or GITHUB_SHA", file=sys.stderr)
                return 2
            interpreter, pip_version, tools_version = _toolchain_versions()
            interpreter = args.interpreter or interpreter
            pip_version = args.pip or pip_version
            tools_version = args.pip_tools or tools_version
            if not interpreter or not pip_version or not tools_version:
                print("emit-validation requires the pinned compiler on sys.path", file=sys.stderr)
                return 2
            if pip_version != maintenance_common.PINNED_PIP or tools_version != maintenance_common.PINNED_PIP_TOOLS:
                print("emit-validation compiler does not match pins", file=sys.stderr)
                return 2
            record = maintenance_common.build_validation_record(
                source_head=source_head,
                candidate=candidate,
                interpreter=interpreter,
                pip_version=pip_version,
                pip_tools_version=tools_version,
                digests=digests,
                run_id=run_id,
                run_attempt=run_attempt,
            )
            rendered = maintenance_common.notice(maintenance_common.VALIDATION_NOTICE, record)
            if not rendered:
                print("validation notice exceeds bound", file=sys.stderr)
                return 2
            print(rendered)
            return 0
        published_head = (args.published_head or "").strip().lower()
        if not maintenance_common.SHA_RE.fullmatch(published_head):
            print("emit-publication requires --published-head", file=sys.stderr)
            return 2
        pull_number = _positive_int(args.pull_number)
        if pull_number is None:
            print("emit-publication requires --pull-number", file=sys.stderr)
            return 2
        branch = args.branch or ""
        if not branch:
            print("emit-publication requires --branch", file=sys.stderr)
            return 2
        pr_author = args.pr_author or ""
        commit_identity = args.commit_identity or str(
            ((profile.get("publication_evidence") or {}) if isinstance(profile.get("publication_evidence"), dict) else {}).get("commit_identity")
            or "github-actions[bot]"
        )
        run_actor = args.run_actor or os.environ.get("GITHUB_ACTOR") or ""
        if not pr_author or not commit_identity or not run_actor:
            print("emit-publication requires distinct actor/author/commit identities", file=sys.stderr)
            return 2
        record = maintenance_common.build_publication_record(
            run_id=run_id,
            run_attempt=run_attempt,
            pull_number=pull_number,
            published_head=published_head,
            branch=branch,
            digests=digests,
            pr_author=pr_author,
            commit_identity=commit_identity,
            run_actor=run_actor,
        )
        rendered = maintenance_common.notice(maintenance_common.PUBLICATION_NOTICE, record)
        if not rendered:
            print("publication notice exceeds bound", file=sys.stderr)
            return 2
        print(rendered)
        return 0

    if args.write_pin:
        version = args.candidate or (json.loads(Path(args.fixture).read_text(encoding="utf-8")).get("candidate") if args.fixture else "")
        if not version:
            print("write-pin requires --candidate", file=sys.stderr)
            return 2
        maintenance.parse_version(version)
        rewrite_pin(pin_path, version)
        print(json.dumps({"status": "rewritten", "candidate": version, "file": pin_rel}))
        return 0

    if args.fixture:
        data = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        current = maintenance.parse_version(str(data.get("current") or pin_path.read_text(encoding="utf-8")))
        result = maintenance.select_python_candidate(
            current,
            data.get("manifest") or [],
            soak_days=int(data.get("soak_days") or profile.get("python", {}).get("soak_days_default") or 30),
            now=maintenance.parse_iso_date(data.get("now")) or datetime.now(timezone.utc),
            ignore_soak=bool(data.get("ignore_soak")),
            force=data.get("force"),
        )
        result["docs_missing_ok"] = not bool(list(profile.get("optional_docs") or [])) or True
        result["optional_docs_present"] = optional_docs_present(profile, root)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        current = maintenance.read_pin(pin_path)
        soak = args.soak_days or int(profile.get("python", {}).get("soak_days_default") or 30)
        dates, date_state, date_detail = maintenance_common.fetch_release_dates(
            cache_path=Path(args.release_date_cache) if args.release_date_cache else None
        )
        manifest, date_report = maintenance_common.apply_release_dates(manifest, dates, date_state)
        date_report["detail"] = date_detail
        result = maintenance.select_python_candidate(
            current,
            manifest,
            soak_days=soak,
            ignore_soak=args.ignore_soak,
            force=args.force or None,
        )
        result["release_dates"] = date_report
        result["optional_docs_present"] = optional_docs_present(profile, root)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    print("live proposer requires --fixture or --manifest; refusing implicit GitHub writes", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
