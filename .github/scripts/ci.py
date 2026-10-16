#!/usr/bin/env python3
"""Explicit CI command registry for development and production profiles.

Every tests/test_*.py file must be registered and executed. Production
profiles skip optional documentation checks. This adapter never posts,
never uses production secrets, and never writes GitHub state.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import maintenance  # noqa: E402
import maintenance_common  # noqa: E402

REPO_ROOT = maintenance.REPO_ROOT
TEST_FILE_RE = re.compile(r"^test_.*\.py$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USES_LINE = re.compile(r"uses:\s*(\S+?)@(\S+)")


def discover_tests(root: Path) -> list[str]:
    tests_dir = root / "tests"
    found = sorted(
        p.name for p in tests_dir.iterdir()
        if p.is_file() and TEST_FILE_RE.match(p.name)
    )
    return found


def registered_tests(profile: dict) -> list[str]:
    names: list[str] = []
    commands = profile.get("test_commands") or {}
    for group in ("application", "maintenance"):
        for cmd in commands.get(group) or []:
            if len(cmd) >= 2 and str(cmd[1]).startswith("tests/"):
                names.append(Path(cmd[1]).name)
    return names


def ensure_all_tests_registered(root: Path, profile: dict) -> None:
    found = set(discover_tests(root))
    registered = set(registered_tests(profile))
    missing = sorted(found - registered)
    extra = sorted(registered - found)
    if missing:
        raise SystemExit(f"unregistered test files: {missing}")
    if extra:
        raise SystemExit(f"registered tests missing on disk: {extra}")


def run_cmd(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> int:
    print("+", " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=str(cwd), env=env)
    return int(completed.returncode)


def group_application(root: Path, profile: dict) -> int:
    compile_cmd = profile.get("test_commands", {}).get("compile") or [
        "python", "-m", "compileall", "-q", "testing area", "tests", ".github/scripts",
    ]
    code = run_cmd(list(compile_cmd), cwd=root)
    if code:
        return code
    for cmd in profile.get("test_commands", {}).get("application") or []:
        code = run_cmd(list(cmd), cwd=root)
        if code:
            return code
    return 0


def group_maintenance(root: Path, profile: dict) -> int:
    for cmd in profile.get("test_commands", {}).get("maintenance") or []:
        code = run_cmd(list(cmd), cwd=root)
        if code:
            return code
    ruff = profile.get("ruff") or {}
    paths = list(ruff.get("paths") or [])
    existing = [p for p in paths if (root / p).exists()]
    if existing:
        code = run_cmd(["python", "-m", "ruff", "check", *existing], cwd=root)
        if code:
            return code
    return 0


def _normalize_lock(path: Path) -> str:
    return maintenance.normalize_compile_header(path.read_text(encoding="utf-8"))


def _github_error(title: str, message: str) -> None:
    safe = message.replace("\n", " ").replace("\r", " ")[:240]
    print(f"::error title={title}::{safe}", flush=True)


def _lock_fingerprint(text: str) -> str:
    lines = text.splitlines()
    pkgs = sum(1 for ln in lines if re.match(r"^[A-Za-z0-9_.-]+==", ln))
    hashes = sum(1 for ln in lines if "--hash=" in ln)
    directives = sum(1 for ln in lines if ln.startswith("--") or ln.startswith("-c "))
    return f"lines={len(lines)} pkgs={pkgs} hashes={hashes} dirs={directives}"


def _first_diff_line(before: str, after: str) -> str:
    a, b = before.splitlines(), after.splitlines()
    for index, (left, right) in enumerate(zip(a, b), start=1):
        if left != right:
            snippet = right[:80] if right else left[:80]
            return f"line {index}: {snippet}"
    if len(a) != len(b):
        return f"length {len(a)}->{len(b)}"
    return "no-line-delta"


def _lock_diff(before: str, after: str, name: str) -> None:
    lines = list(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{name} (before)",
            tofile=f"{name} (after)",
            n=1,
        )
    )
    for line in lines[:120]:
        sys.stderr.write(line if line.endswith("\n") else line + "\n")
    if len(lines) > 120:
        print(f"... diff truncated ({len(lines)} lines)", file=sys.stderr)
    _github_error(
        "lock-not-byte-stable",
        f"{name} {_lock_fingerprint(before)} vs {_lock_fingerprint(after)}; {_first_diff_line(before, after)}",
    )


def _print_lock_toolchain() -> None:
    print("lock-consistency python", sys.version.replace("\n", " "), flush=True)
    print(
        "lock-consistency pinned",
        f"pip=={maintenance_common.PINNED_PIP}",
        f"pip-tools=={maintenance_common.PINNED_PIP_TOOLS}",
        flush=True,
    )
    try:
        import pip
        print("lock-consistency pip", getattr(pip, "__version__", "?"), flush=True)
    except Exception as exc:
        print("lock-consistency pip unavailable:", exc, flush=True)
    try:
        import piptools
        print(
            "lock-consistency piptools",
            getattr(piptools, "__version__", "present"),
            flush=True,
        )
    except Exception as exc:
        print("lock-consistency piptools unavailable:", exc, flush=True)


def _compiler_pin_failures(root: Path, profile: dict) -> list[str]:
    """Require the pinned compiler to appear in the lock that records it."""
    pinned_pip, pinned_tools = maintenance_common.compiler_pins(profile)
    problems: list[str] = []
    if pinned_pip != maintenance_common.PINNED_PIP or pinned_tools != maintenance_common.PINNED_PIP_TOOLS:
        problems.append(
            f"profile compiler pip=={pinned_pip} pip-tools=={pinned_tools} "
            f"does not match helper pins pip=={maintenance_common.PINNED_PIP} "
            f"pip-tools=={maintenance_common.PINNED_PIP_TOOLS}"
        )
    dev = root / "requirements-dev.txt"
    if not dev.is_file():
        problems.append("missing requirements-dev.txt (compiler pins live there)")
        return problems
    text = dev.read_text(encoding="utf-8")
    if f"pip=={pinned_pip}" not in text:
        problems.append(f"requirements-dev.txt must contain pip=={pinned_pip}")
    if f"pip-tools=={pinned_tools}" not in text:
        problems.append(f"requirements-dev.txt must contain pip-tools=={pinned_tools}")
    return problems


def group_lock_consistency(root: Path, profile: dict) -> int:
    runtime = root / "requirements.txt"
    dev = root / "requirements-dev.txt"
    if not runtime.is_file():
        print("missing requirements.txt", file=sys.stderr)
        return 1
    if " --hash=" not in runtime.read_text(encoding="utf-8"):
        print("requirements.txt is not a hashed lock", file=sys.stderr)
        return 1
    pin_problems = _compiler_pin_failures(root, profile)
    if pin_problems:
        for problem in pin_problems:
            print(problem, file=sys.stderr)
            _github_error("compiler-pin-mismatch", problem)
        return 1
    _print_lock_toolchain()
    before_runtime = _normalize_lock(runtime)
    before_dev = _normalize_lock(dev) if dev.is_file() else ""
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    compile_cmd = list(profile.get("compile_command") or [])
    if not compile_cmd:
        print("compile_command missing from profile", file=sys.stderr)
        return 1
    env["CUSTOM_COMPILE_COMMAND"] = " ".join(compile_cmd)
    argv = list(compile_cmd)
    if argv and argv[0] == "python":
        argv[0] = sys.executable
    code = run_cmd(argv, cwd=root, env=env)
    if code:
        _github_error("pip-compile-failed", f"runtime compile exit {code} argv={' '.join(argv[:6])}")
        return code
    after_runtime = _normalize_lock(runtime)
    if after_runtime != before_runtime:
        print(
            "requirements.txt regeneration was not byte-stable after compiler-header normalization",
            file=sys.stderr,
        )
        _lock_diff(before_runtime, after_runtime, "requirements.txt")
        return 1
    dev_cmd = list(profile.get("dev_compile_command") or [])
    if dev_cmd and (root / "requirements-dev.in").is_file():
        env["CUSTOM_COMPILE_COMMAND"] = " ".join(dev_cmd)
        dev_argv = list(dev_cmd)
        if dev_argv and dev_argv[0] == "python":
            dev_argv[0] = sys.executable
        code = run_cmd(dev_argv, cwd=root, env=env)
        if code:
            _github_error("pip-compile-failed", f"dev compile exit {code}")
            return code
        after_dev = _normalize_lock(dev)
        if after_dev != before_dev:
            print(
                "requirements-dev.txt regeneration was not byte-stable after compiler-header normalization",
                file=sys.stderr,
            )
            _lock_diff(before_dev, after_dev, "requirements-dev.txt")
            return 1
    return 0


def _parse_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ImportError:
        print("PyYAML is required for workflow validation (dev dependency)", file=sys.stderr)
        raise
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _iter_steps(doc: dict):
    jobs = doc.get("jobs") or {}
    if not isinstance(jobs, dict):
        return
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps") or []
        if not isinstance(steps, list):
            continue
        for step in steps:
            if isinstance(step, dict):
                yield job_name, job, step


def group_workflow_security(root: Path, profile: dict) -> int:
    workflows = sorted((root / ".github" / "workflows").glob("*.yml"))
    errors: list[str] = []
    if not workflows:
        errors.append("no workflow files")
    forbidden_lock = root / ".github" / "workflows" / "actions.lock"
    if forbidden_lock.exists():
        errors.append("Actions workflow lockfile is forbidden")
    for path in workflows:
        try:
            doc = _parse_yaml(path)
        except Exception as exc:  # includes YAMLError
            errors.append(f"{path.name}: YAML parse failed: {exc}")
            continue
        if not isinstance(doc, dict):
            errors.append(f"{path.name}: workflow is not a mapping")
            continue
        jobs = doc.get("jobs") or {}
        if not isinstance(jobs, dict) or not jobs:
            errors.append(f"{path.name}: no jobs")
            continue
        on = doc.get("on") or doc.get(True)
        workflow_name = str(doc.get("name") or path.name)
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                errors.append(f"{path.name} ({workflow_name}): job {job_name} malformed")
                continue
            if "timeout-minutes" not in job:
                errors.append(f"{path.name} ({workflow_name}): job {job_name} missing timeout-minutes")
        for job_name, job, step in _iter_steps(doc):
            uses = str(step.get("uses") or "")
            if path.name == "maintenance_merge.yml" and uses.startswith("actions/checkout"):
                with_ = step.get("with") if isinstance(step.get("with"), dict) else {}
                persist = with_.get("persist-credentials")
                if persist is not False and str(persist).lower() != "false":
                    errors.append("merge controller checkout must set persist-credentials: false")
                ref = str(with_.get("ref") or "")
                if "head" in ref and "default_branch" not in ref:
                    errors.append("merge controller must not check out PR head")
        text = path.read_text(encoding="utf-8")
        for match in USES_LINE.finditer(text):
            action, ref = match.group(1), match.group(2).strip()
            ref = ref.split("#", 1)[0].strip()
            if ref in {"latest", "main", "master"} or re.fullmatch(r"v\d+", ref):
                errors.append(f"{path.name}: floating action ref {action}@{ref}")
            elif not SHA_RE.fullmatch(ref.lower()):
                errors.append(f"{path.name}: action ref is not a 40-char SHA: {action}@{ref}")
        if path.name in {"reddit_monitor.yml", "twitter_monitor.yml"}:
            if "cancel-in-progress: false" not in text:
                errors.append(f"{path.name}: cancel-in-progress must stay false")
            if re.search(r"^\s+schedule:", text, re.M) and "DISABLED" not in text:
                errors.append(f"{path.name}: native schedule must stay disabled")
        if path.name == "ci.yml":
            perms = doc.get("permissions")
            if perms != {"contents": "read"} and perms != "read-all":
                # contents: read is the required least privilege for PR CI
                if not (isinstance(perms, dict) and perms.get("contents") == "read" and set(perms) <= {"contents"}):
                    errors.append("ci.yml must use contents: read only")
            if "pull_request_target" in text:
                errors.append("ci.yml must not use pull_request_target")
            if "secrets." in text and "github.token" not in text.lower():
                # CI should not wire production monitor secrets
                if "DISCORD_WEBHOOK" in text or "BUMP_PAT" in text:
                    errors.append("ci.yml must not use production secrets")
        if path.name == "maintenance_merge.yml":
            if "actions/checkout" in text and "pull_request" in str(on):
                if "ref:" not in text and "default_branch" not in text:
                    errors.append("merge controller must not check out PR head")
        if "gh-actions-lock" in text or "actions.lock" in text:
            errors.append(f"{path.name}: Actions lockfile integration is forbidden")
        colon_run = re.search(r"^\s+run:\s+.*:", text, re.M)
        if colon_run and "run: |" not in text[max(0, colon_run.start() - 80):colon_run.end()]:
            # pip arguments with colons must use block scalars; flag likely offenders
            line = colon_run.group(0)
            if "--only-binary" in line or "python-version:" in line:
                errors.append(f"{path.name}: colon-bearing run value must use a block scalar")
    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        return 1
    actionlint = profile.get("actionlint") or {}
    code = maybe_run_actionlint(root, actionlint)
    if code:
        return code
    return 0


def maybe_run_actionlint(root: Path, spec: dict) -> int:
    """Run pinned actionlint. Download or skip failures are not a successful gate."""
    url = str(spec.get("url") or "")
    sha256 = str(spec.get("sha256") or "")
    if not url or not sha256:
        print("actionlint pin missing from maintenance profile", file=sys.stderr)
        return 1
    if os.environ.get("SKIP_ACTIONLINT") == "1":
        print("SKIP_ACTIONLINT is not a successful bypass", file=sys.stderr)
        return 1
    dest_dir = Path(tempfile.mkdtemp(prefix="actionlint-"))
    archive = dest_dir / "actionlint.tgz"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "news-express-ci"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            archive.write_bytes(resp.read())
    except Exception as exc:
        print(
            f"actionlint download failed ({exc}); required validator did not run",
            file=sys.stderr,
        )
        return 1
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != sha256:
        print(f"actionlint checksum mismatch: {digest} != {sha256}", file=sys.stderr)
        return 1
    with tarfile.open(archive) as tar:
        tar.extractall(dest_dir)
    binary = dest_dir / "actionlint"
    if not binary.exists():
        print("actionlint binary missing from archive", file=sys.stderr)
        return 1
    binary.chmod(0o755)
    return run_cmd([str(binary), "-color"], cwd=root)


def group_docs(root: Path, profile: dict, require_docs: bool) -> int:
    docs = [root / rel for rel in (profile.get("optional_docs") or [])]
    missing = [str(p.relative_to(root)) for p in docs if not p.exists()]
    if missing and require_docs:
        print("missing development docs:", ", ".join(missing), file=sys.stderr)
        return 1
    if missing and not require_docs:
        print("optional docs absent (production profile) — OK:", ", ".join(missing))
    return 0


def final_gate(results: dict[str, int]) -> int:
    """Succeed only when every mandatory dependency actually succeeded."""
    failed = [name for name, code in results.items() if code != 0]
    if failed:
        print("maintenance-ci failed because:", ", ".join(failed), file=sys.stderr)
        return 1
    if any(code is None for code in results.values()):
        print("maintenance-ci failed: a mandatory check did not run", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("development", "production"), default="development")
    parser.add_argument(
        "--group",
        choices=("application", "maintenance", "lock-consistency", "workflow-security", "docs", "all", "final"),
        default="all",
    )
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--maintenance-json", default=str(maintenance.DEFAULT_PROFILE))
    parser.add_argument("--results-json", default="", help="for --group final")
    args = parser.parse_args(argv)

    root = Path(args.root)
    profile = maintenance.load_profile(args.maintenance_json)
    os.chdir(root)
    ensure_all_tests_registered(root, profile)

    require_docs = bool((profile.get("profiles") or {}).get(args.profile, {}).get("require_docs"))
    if args.profile == "production":
        require_docs = False

    if args.group == "final":
        import json
        results = json.loads(Path(args.results_json).read_text(encoding="utf-8"))
        return final_gate(results)

    dispatch = {
        "application": lambda: group_application(root, profile),
        "maintenance": lambda: group_maintenance(root, profile),
        "lock-consistency": lambda: group_lock_consistency(root, profile),
        "workflow-security": lambda: group_workflow_security(root, profile),
        "docs": lambda: group_docs(root, profile, require_docs),
    }
    if args.group != "all":
        return dispatch[args.group]()

    results = {}
    for name, fn in dispatch.items():
        if name == "docs" and args.profile == "production":
            results[name] = group_docs(root, profile, False)
            continue
        results[name] = fn()
        if results[name] != 0 and name != "docs":
            return results[name]
    return final_gate({k: v for k, v in results.items() if k != "docs" or require_docs})


if __name__ == "__main__":
    sys.exit(main())
