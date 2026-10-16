"""Offline tests for the portable maintenance_common candidate.

These cover producer identity, security evidence, publication provenance,
python.org soak dates, and compiler pins. Caller-level decide_merge probes
live in test_maintenance.py so a green helper fixture cannot hide a broken
merge controller.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".github" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import maintenance_common  # noqa: E402

SHA = "a" * 40
REPO = "uesu/News-Express"


class RepoAssociationTests(unittest.TestCase):
    def test_missing_and_fork(self):
        pr = {"head": {"sha": SHA, "ref": "x"}, "base": {"ref": "main"}}
        self.assertEqual(
            maintenance_common.repo_association_failure(pr, REPO),
            "missing-repo-association",
        )
        pr = {
            "head": {"repo": {"full_name": "alice/fork"}},
            "base": {"repo": {"full_name": REPO}},
        }
        self.assertEqual(
            maintenance_common.repo_association_failure(pr, REPO),
            "cross-fork-head",
        )
        pr = {
            "head": {"repo": {"full_name": REPO}},
            "base": {"repo": {"full_name": REPO}},
        }
        self.assertEqual(maintenance_common.repo_association_failure(pr, REPO), "")


class ProducerTests(unittest.TestCase):
    def test_foreign_details_url_is_unresolvable(self):
        self.assertIsNone(
            maintenance_common.parse_check_run_identity(
                "https://github.com/evil/fork/actions/runs/2/job/3", REPO
            )
        )
        self.assertEqual(
            maintenance_common.parse_check_run_identity(
                "https://github.com/uesu/News-Express/actions/runs/2/job/3", REPO
            ),
            (2, 3),
        )

    def test_collect_records_job_api_failure(self):
        def get_json(url: str) -> tuple[int, Any]:
            return 403, {"message": "no"}

        evidence = maintenance_common.collect_producer_evidence(
            "uesu",
            "News-Express",
            [{
                "id": 1,
                "name": "application",
                "details_url": "https://github.com/uesu/News-Express/actions/runs/2/job/3",
            }],
            ["application"],
            get_json,
        )
        self.assertEqual(evidence["application"]["error"], "job-api:403")

    def test_verify_requires_mutual_check_run_link(self):
        producers = {"application": {"workflow": ".github/workflows/ci.yml", "job": "application"}}
        found = {
            "workflow": ".github/workflows/ci.yml",
            "job": "application",
            "check_run_id": 1,
            "run_id": 2,
            "run_record_id": 2,
            "job_id": 3,
            "job_record_id": 3,
            "job_run_id": 2,
            "job_check_run_url": "https://api.github.com/repos/uesu/News-Express/check-runs/99",
            "run_attempt": 1,
            "job_run_attempt": 1,
            "head_sha": SHA,
            "job_head_sha": SHA,
            "job_status": "completed",
            "job_conclusion": "success",
            "run_status": "completed",
            "run_conclusion": "success",
        }
        result = maintenance_common.verify_check_producers(
            {"application": found},
            expected_names=["application"],
            head_sha=SHA,
            producers=producers,
            repository=REPO,
        )
        self.assertEqual(result["state"], "failed")
        self.assertIn("producer-check-run-id-mismatch", result["reason"])

    def test_stale_attempt_and_unapproved_job_fail(self):
        producers = {"application": {"workflow": ".github/workflows/ci.yml", "job": "application"}}
        found = {
            "workflow": ".github/workflows/ci.yml",
            "job": "application",
            "check_run_id": 1,
            "run_id": 2,
            "run_record_id": 2,
            "job_id": 3,
            "job_record_id": 3,
            "job_run_id": 2,
            "job_check_run_url": "https://api.github.com/repos/uesu/News-Express/check-runs/1",
            "run_attempt": 2,
            "job_run_attempt": 1,
            "head_sha": SHA,
            "job_head_sha": SHA,
            "job_status": "completed",
            "job_conclusion": "success",
            "run_status": "completed",
            "run_conclusion": "success",
        }
        result = maintenance_common.verify_check_producers(
            {"application": found},
            expected_names=["application"],
            head_sha=SHA,
            producers=producers,
            repository=REPO,
        )
        self.assertEqual(result["reason"], "producer-attempt-mismatch:application")
        found["job_run_attempt"] = 2
        found["job"] = "other"
        result = maintenance_common.verify_check_producers(
            {"application": found},
            expected_names=["application"],
            head_sha=SHA,
            producers=producers,
            repository=REPO,
        )
        self.assertEqual(result["reason"], "unapproved-producer-job:application")

    def test_no_producers_configured_fails(self):
        result = maintenance_common.verify_check_producers(
            {},
            expected_names=["application"],
            head_sha=SHA,
            producers={},
            repository=REPO,
        )
        self.assertEqual(result["reason"], "no-approved-producers-configured")


class SecurityTests(unittest.TestCase):
    def test_disabled_vs_unconfigured(self):
        mode, kinds = maintenance_common.security_policy({"security_evidence": {"mode": "disabled"}})
        self.assertEqual(mode, "disabled")
        self.assertEqual(kinds, [])
        ready = maintenance_common.verify_security_evidence(None, [], mode="disabled")
        self.assertEqual(ready["reason"], "security-evidence-not-required")
        gap = maintenance_common.verify_security_evidence(None, [], mode="")
        self.assertEqual(gap["reason"], "security-evidence-unconfigured")

    def test_malformed_alert_is_not_zero_open(self):
        count = maintenance_common._count_open_alerts(
            [{"state": "open"}],
            code_scanning=True,
        )
        self.assertIsNone(count)
        count = maintenance_common._count_open_alerts(
            [{"state": "open", "most_recent_instance": {"state": "fixed"}}],
            code_scanning=True,
        )
        self.assertIsNone(count)
        count = maintenance_common._count_open_alerts(
            [{"state": "open", "most_recent_instance": {"state": "open"}}],
            code_scanning=True,
        )
        self.assertEqual(count, 1)

    def test_stale_analysis_is_not_this_head(self):
        def get_pages(url: str) -> tuple[int, Any]:
            if "analyses" in url:
                return 200, [{"commit_sha": "b" * 40, "error": None}]
            return 200, []

        result = maintenance_common.collect_security_evidence(
            "uesu", "News-Express", SHA, ["code-scanning"], get_pages, ref="chore/x"
        )
        self.assertEqual(result["code-scanning"]["state"], "no-analysis-for-head")

    def test_missing_ref_scope_is_not_clean(self):
        def get_pages(url: str) -> tuple[int, Any]:
            if "analyses" in url:
                return 200, [{"commit_sha": SHA, "error": None}]
            return 200, []

        result = maintenance_common.collect_security_evidence(
            "uesu", "News-Express", SHA, ["code-scanning"], get_pages, ref=""
        )
        self.assertEqual(result["code-scanning"]["state"], "missing-ref-scope")

    def test_open_alerts_fail_closed(self):
        result = maintenance_common.verify_security_evidence(
            {"code-scanning": {"state": "ok", "open": 1}},
            ["code-scanning"],
            mode="required",
        )
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["reason"], "unresolved-code-scanning-alerts:1")

    def test_http_403_defers(self):
        result = maintenance_common.verify_security_evidence(
            {"secret-scanning": {"state": "unavailable", "detail": "alerts-http:403"}},
            ["secret-scanning"],
            mode="required",
        )
        self.assertEqual(result["state"], "defer")


class PublicationTests(unittest.TestCase):
    def test_dependabot_skips_and_python_bump_needs_mode(self):
        pr = {"number": 1, "user": {"login": "github-actions[bot]"}, "head": {"sha": SHA, "ref": "chore/python-3.14.9"}}
        skipped = maintenance_common.verify_publication_gate(
            mode="", kind="dependabot", evidence={}, pr=pr
        )
        self.assertEqual(skipped["reason"], "publication-not-applicable")
        gap = maintenance_common.verify_publication_gate(
            mode="", kind="python_bump", evidence={}, pr=pr
        )
        self.assertEqual(gap["reason"], "publication-evidence-unconfigured")
        disabled = maintenance_common.verify_publication_gate(
            mode="disabled", kind="python_bump", evidence={}, pr=pr
        )
        self.assertEqual(disabled["reason"], "publication-evidence-not-required")

    def test_required_mode_rejects_missing_run_and_digest_mismatch(self):
        pr = {
            "number": 9,
            "user": {"login": "news-express-bump"},
            "head": {"sha": SHA, "ref": "chore/python-3.14.9"},
        }
        missing = maintenance_common.verify_publication_gate(
            mode="required",
            kind="python_bump",
            evidence={"repository": REPO},
            pr=pr,
            candidate_version="3.14.9",
            repository=REPO,
        )
        self.assertEqual(missing["reason"], "no-proposer-run")

        run = {
            "id": 44,
            "workflow_id": 7,
            "path": maintenance_common.DEFAULT_PROPOSER_PATH,
            "status": "completed",
            "conclusion": "success",
            "run_attempt": 1,
            "head_sha": "c" * 40,
            "actor": {"login": "github-actions[bot]"},
            "repository": {"full_name": REPO},
            "head_repository": {"full_name": REPO},
        }
        evidence = {
            "repository": REPO,
            "proposer_run": run,
            "proposer_attempt": {
                "id": 44, "run_attempt": 1, "status": "completed",
                "conclusion": "success", "head_sha": "c" * 40,
            },
            "validation_record": {
                "run_id": 44, "run_attempt": 1, "source_head": "c" * 40,
                "candidate_version": "3.14.9", "interpreter": "3.14.9",
                "pip": maintenance_common.PINNED_PIP,
                "pip_tools": maintenance_common.PINNED_PIP_TOOLS,
                "digests": {".python-version": "aaa"},
            },
            "publication_record": {
                "run_id": 44, "run_attempt": 1, "pull_number": 9,
                "published_head": SHA, "branch": "chore/python-3.14.9",
                "pr_author": "news-express-bump",
                "run_actor": "github-actions[bot]",
                "commit_identity": "github-actions[bot]",
                "digests": {".python-version": "bbb"},
            },
            "proposal_digests": {".python-version": "aaa"},
            "expected_commit_identity": "github-actions[bot]",
            "published_commit": {"sha": SHA},
        }
        mismatch = maintenance_common.verify_publication_gate(
            mode="required",
            kind="python_bump",
            evidence=evidence,
            pr=pr,
            candidate_version="3.14.9",
            proposal_files=[".python-version"],
            repository=REPO,
        )
        self.assertEqual(mismatch["reason"], "publication-digest-mismatch:.python-version")


class ReleaseDateTests(unittest.TestCase):
    def test_apply_strips_setup_python_published_at(self):
        manifest = [{
            "version": "3.15.0",
            "stable": True,
            "published_at": "2026-10-01T00:00:00Z",
            "release_date": "2026-10-01T00:00:00Z",
        }]
        enriched, report = maintenance_common.apply_release_dates(manifest, {}, "unavailable")
        self.assertNotIn("published_at", enriched[0])
        self.assertNotIn("release_date", enriched[0])
        self.assertIn("3.15.0", report["stripped_untrusted_dates"])
        self.assertIn("3.15.0", report["unknown"])

    def test_python_org_date_is_the_authority(self):
        manifest = [{
            "version": "3.15.0",
            "published_at": "2099-01-01T00:00:00Z",
        }]
        enriched, report = maintenance_common.apply_release_dates(
            manifest, {"3.15.0": "2026-01-15"}, "ok"
        )
        self.assertEqual(enriched[0]["release_date"], "2026-01-15")
        self.assertEqual(enriched[0]["release_date_source"], "python.org-downloads-api")
        self.assertNotIn("published_at", enriched[0])
        self.assertEqual(report["resolved"], ["3.15.0"])

    def test_fetch_uses_injected_opener_and_cache(self):
        payload = {
            "results": [
                {"name": "Python 3.15.0", "release_date": "2026-01-15T00:00:00Z"},
                {"name": "Not a release", "release_date": "2026-01-01T00:00:00Z"},
            ],
            "next": None,
        }

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return json.dumps(payload).encode("utf-8")

        def opener(url, timeout=10):
            self.assertIn("python.org", url)
            return _Resp()

        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "dates.json"
            dates, state, detail = maintenance_common.fetch_release_dates(
                opener=opener,
                cache_path=cache,
                now=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
            self.assertEqual(state, "ok")
            self.assertEqual(dates["3.15.0"], "2026-01-15")
            self.assertTrue(cache.is_file())
            dates2, state2, _ = maintenance_common.fetch_release_dates(
                opener=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("network")),
                cache_path=cache,
                now=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
            self.assertEqual(state2, "cache")
            self.assertEqual(dates2["3.15.0"], "2026-01-15")

    def test_unavailable_authority_is_not_up_to_date(self):
        def opener(url, timeout=10):
            raise TimeoutError("nope")

        with tempfile.TemporaryDirectory() as tmp:
            dates, state, detail = maintenance_common.fetch_release_dates(
                opener=opener,
                cache_path=Path(tmp) / "missing.json",
            )
        self.assertEqual(dates, {})
        self.assertEqual(state, "unavailable")
        self.assertIn("TimeoutError", detail)


class CompilerPinTests(unittest.TestCase):
    def test_pins_match_dev_lock_and_profile(self):
        self.assertEqual(maintenance_common.PINNED_PIP, "26.1.1")
        self.assertEqual(maintenance_common.PINNED_PIP_TOOLS, "7.5.3")
        profile = json.loads((ROOT / ".github" / "maintenance.json").read_text(encoding="utf-8"))
        pip, tools = maintenance_common.compiler_pins(profile)
        self.assertEqual((pip, tools), (maintenance_common.PINNED_PIP, maintenance_common.PINNED_PIP_TOOLS))
        text = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        self.assertIn(f"pip=={pip}", text)
        self.assertIn(f"pip-tools=={tools}", text)


class CiCompilerPinTests(unittest.TestCase):
    def test_lock_consistency_rejects_missing_compiler_pin(self):
        import ci as ci_mod
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements.txt").write_text("pkg==1.0 --hash=sha256:aa\n", encoding="utf-8")
            (root / "requirements-dev.txt").write_text("ruff==0.13.2 --hash=sha256:bb\n", encoding="utf-8")
            problems = ci_mod._compiler_pin_failures(root, {})
            self.assertTrue(any("pip==" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
