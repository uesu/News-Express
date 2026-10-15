"""Offline maintenance policy tests — no GitHub writes, no posting."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".github" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import maintenance  # noqa: E402
import python_version_bump  # noqa: E402

SHA = "a" * 40
SHA2 = "b" * 40


def _pr(*, login="dependabot[bot]", sha=SHA, ref="dependabot/pip/foo", draft=False,
        labels=None, mergeable=True, mergeable_state="clean", base="main"):
    return {
        "number": 12,
        "state": "open",
        "draft": draft,
        "html_url": "https://example.test/pr/12",
        "mergeable": mergeable,
        "mergeable_state": mergeable_state,
        "user": {"login": login},
        "head": {"sha": sha, "ref": ref},
        "base": {"ref": base},
        "labels": labels or [],
    }


def _snapshot(**overrides):
    data = {
        "repository": "uesu/News-Express",
        "head_sha": SHA,
        "pull_request": _pr(),
        "checks": [{
            "id": 1, "name": "application", "head_sha": SHA, "status": "completed",
            "conclusion": "success", "app": {"slug": "github-actions"},
        }],
        "files": [{"filename": "requirements.txt", "patch": "-aiohttp==3.14.4\n+aiohttp==3.14.5\n"}],
        "reviews": [],
        "legacy_statuses": [],
        "risk": {"risk": "routine", "auto_eligible": True, "reason": "package-patch-or-minor"},
        "variables": {"AUTO_MERGE_DEPENDABOT": "yes", "AUTO_MERGE_PYTHON_BUMP": "yes"},
        "policy": {
            "repository": "uesu/News-Express",
            "default_branch": "main",
            "mandatory_check_names": ["application"],
            "human_review_labels": ["review-required", "do-not-merge", "hold"],
            "updater_identities": {
                "dependabot": {"login": "dependabot[bot]", "auto_merge_var": "AUTO_MERGE_DEPENDABOT"},
                "python_bump": {
                    "login": "github-actions[bot]",
                    "auto_merge_var": "AUTO_MERGE_PYTHON_BUMP",
                    "branch_prefix": "chore/python-",
                    "allowed_files": [".python-version"],
                },
            },
            "allowed_merge_method": "squash",
        },
    }
    data.update(overrides)
    return data


class VersionAndSelectTests(unittest.TestCase):
    def test_patch_is_auto_eligible(self):
        current = maintenance.parse_version("3.14.8")
        manifest = [{
            "version": "3.14.9",
            "stable": True,
            "release_url": "https://example.test/3.14.9",
            "files": [{"platform": "linux", "arch": "x64"}],
        }]
        result = maintenance.select_python_candidate(current, manifest)
        self.assertEqual(result["status"], "proposed")
        self.assertEqual(result["kind"], "patch")
        self.assertTrue(result["auto_eligible"])

    def test_next_minor_needs_review_after_soak(self):
        current = maintenance.parse_version("3.14.8")
        manifest = [{
            "version": "3.15.0",
            "stable": True,
            "release_date": "2026-01-01T00:00:00Z",
            "files": [{"platform": "linux", "arch": "x64"}],
        }]
        result = maintenance.select_python_candidate(
            current, manifest, soak_days=30,
            now=maintenance.parse_iso_date("2026-03-01T00:00:00Z"),
        )
        self.assertEqual(result["status"], "review-required")
        self.assertEqual(result["kind"], "minor")
        self.assertFalse(result["auto_eligible"])

    def test_minor_inside_soak_is_deferred(self):
        current = maintenance.parse_version("3.14.8")
        manifest = [{
            "version": "3.15.0",
            "stable": True,
            "release_date": "2026-09-20T00:00:00Z",
            "files": [{"platform": "linux", "arch": "x64"}],
        }]
        result = maintenance.select_python_candidate(
            current, manifest, soak_days=30,
            now=maintenance.parse_iso_date("2026-09-25T00:00:00Z"),
        )
        self.assertEqual(result["status"], "deferred")
        self.assertIn("soak", result["reason"])

    def test_skip_minor_and_major_are_not_auto(self):
        current = maintenance.parse_version("3.14.8")
        forced = maintenance.select_python_candidate(
            current,
            [{"version": "3.16.0", "stable": True, "files": [{"platform": "linux", "arch": "x64"}]}],
            force="3.16.0",
        )
        self.assertEqual(forced["status"], "review-required")
        self.assertFalse(forced["auto_eligible"])
        major = maintenance.select_python_candidate(
            current,
            [{"version": "4.0.0", "stable": True, "files": [{"platform": "linux", "arch": "x64"}]}],
            force="4.0.0",
        )
        self.assertEqual(major["status"], "review-required")
        self.assertFalse(major["auto_eligible"])

    def test_forced_override_validates_direction_archive_and_policy(self):
        current = maintenance.parse_version("3.14.8")
        linux = [{"platform": "linux", "arch": "x64"}]
        empty = maintenance.select_python_candidate(current, [], force="3.14.7")
        self.assertNotEqual(empty["status"], "proposed")
        self.assertNotEqual(empty.get("kind"), "patch")
        self.assertFalse(empty.get("auto_eligible"))
        self.assertEqual(empty["reason"], "override-unavailable")
        downgrade = maintenance.select_python_candidate(
            current,
            [{"version": "3.14.7", "stable": True, "files": linux}],
            force="3.14.7",
        )
        self.assertEqual(downgrade["status"], "review-required")
        self.assertEqual(downgrade["kind"], "downgrade")
        self.assertFalse(downgrade["auto_eligible"])
        prerelease = maintenance.select_python_candidate(current, [], force="3.14.9rc1")
        self.assertEqual(prerelease["status"], "failed")
        self.assertIn("override-invalid", prerelease["reason"])
        same = maintenance.select_python_candidate(current, [], force="3.14.8")
        self.assertEqual(same["status"], "up-to-date")
        win_only = maintenance.select_python_candidate(
            current,
            [{"version": "3.14.9", "stable": True, "files": [{"platform": "win32", "arch": "x64"}]}],
            force="3.14.9",
        )
        self.assertEqual(win_only["status"], "failed")
        self.assertEqual(win_only["reason"], "override-unavailable")
        patch = maintenance.select_python_candidate(
            current,
            [{"version": "3.14.9", "stable": True, "files": linux}],
            force="3.14.9",
        )
        self.assertEqual(patch["status"], "proposed")
        self.assertEqual(patch["kind"], "patch")
        self.assertTrue(patch["auto_eligible"])
        self.assertEqual(
            maintenance.classify_python_change("3.14.8", "3.14.7")["auto_eligible"],
            False,
        )
        self.assertEqual(maintenance.classify_python_change("3.14.8", "3.14.7")["kind"], "downgrade")

    def test_prerelease_manifest_entries_are_ignored(self):
        current = maintenance.parse_version("3.14.8")
        manifest = [{
            "version": "3.14.9rc1",
            "stable": True,
            "files": [{"platform": "linux", "arch": "x64"}],
        }]
        result = maintenance.select_python_candidate(current, manifest)
        self.assertEqual(result["status"], "up-to-date")

    def test_package_and_action_classification(self):
        self.assertEqual(maintenance.classify_package_update("1.2.3", "1.2.4")["risk"], "routine")
        self.assertEqual(maintenance.classify_package_update("1.2.3", "2.0.0")["risk"], "review-required")
        self.assertEqual(maintenance.classify_package_update("0.4.0", "0.5.0")["risk"], "review-required")
        self.assertEqual(
            maintenance.classify_action_update(SHA, SHA2, old_action="actions/checkout",
                                               new_action="actions/checkout",
                                               comment_old="v7", comment_new="v7")["risk"],
            "routine",
        )
        self.assertEqual(
            maintenance.classify_action_update(SHA, SHA2, old_action="actions/checkout",
                                               new_action="actions/checkout",
                                               comment_old="v7", comment_new="v8")["risk"],
            "review-required",
        )
        grouped = maintenance.highest_risk([
            {"risk": "routine", "auto_eligible": True},
            {"risk": "review-required", "auto_eligible": False},
        ])
        self.assertEqual(grouped["risk"], "review-required")
        self.assertFalse(grouped["auto_eligible"])

    def test_grouped_lock_uses_highest_member_risk(self):
        files = [{
            "filename": "requirements.txt",
            "patch": (
                "-aiohttp==3.14.5\n+aiohttp==4.0.0\n"
                "-idna==3.19\n+idna==3.20\n"
            ),
        }]
        risk = maintenance.snapshot_risk_from_files(files, "dependabot")
        self.assertEqual(risk["risk"], "review-required")
        self.assertGreaterEqual(risk["members"], 2)
        self.assertFalse(risk["auto_eligible"])

    def test_hash_only_and_truncated_lock_are_review(self):
        hashed = maintenance.snapshot_risk_from_files([{
            "filename": "requirements.txt",
            "patch": "-    --hash=sha256:aaa\n+    --hash=sha256:bbb\n",
        }], "dependabot")
        self.assertEqual(hashed["risk"], "review-required")
        truncated = maintenance.snapshot_risk_from_files([{
            "filename": "requirements.txt",
            "patch": "",
        }], "dependabot")
        self.assertEqual(truncated["risk"], "review-required")

    def test_minor_date_lookup_enriches_missing_manifest_dates(self):
        current = maintenance.parse_version("3.14.8")
        manifest = [{
            "version": "3.15.0",
            "stable": True,
            "files": [{"platform": "linux", "arch": "x64"}],
        }]
        deferred = maintenance.select_python_candidate(current, manifest)
        self.assertEqual(deferred["status"], "deferred")
        soaked = maintenance.select_python_candidate(
            current, manifest, soak_days=30,
            now=maintenance.parse_iso_date("2026-03-01T00:00:00Z"),
            date_lookup=lambda _version, _entry: "2026-01-01T00:00:00Z",
        )
        self.assertEqual(soaked["status"], "review-required")
        self.assertEqual(soaked["kind"], "minor")


class CheckClassificationTests(unittest.TestCase):
    def test_zero_checks_fail(self):
        result = maintenance.classify_checks(
            [], expected_names=["application"], head_sha=SHA)
        self.assertEqual(result["state"], "failed")

    def test_skipped_neutral_cancelled_do_not_count(self):
        for conclusion in ("skipped", "neutral", "cancelled", "failure"):
            result = maintenance.classify_checks(
                [{"id": 1, "name": "application", "head_sha": SHA, "status": "completed",
                  "conclusion": conclusion, "app": {"slug": "github-actions"}}],
                expected_names=["application"], head_sha=SHA)
            self.assertEqual(result["state"], "failed", conclusion)

    def test_pending_stays_pending(self):
        result = maintenance.classify_checks(
            [{"id": 1, "name": "application", "head_sha": SHA, "status": "in_progress",
              "app": {"slug": "github-actions"}}],
            expected_names=["application"], head_sha=SHA)
        self.assertEqual(result["state"], "pending")

    def test_unrelated_and_foreign_ignored_or_rejected(self):
        result = maintenance.classify_checks(
            [{"id": 1, "name": "unrelated", "head_sha": SHA, "status": "completed",
              "conclusion": "success", "app": {"slug": "github-actions"}}],
            expected_names=["application"], head_sha=SHA)
        self.assertEqual(result["state"], "failed")
        foreign = maintenance.classify_checks(
            [{"id": 1, "name": "application", "head_sha": SHA, "status": "completed",
              "conclusion": "success", "app": {"slug": "not-github"}}],
            expected_names=["application"], head_sha=SHA)
        self.assertEqual(foreign["state"], "failed")
        self.assertIn("untrusted-app", foreign["reason"])

    def test_stale_sha_is_ignored(self):
        result = maintenance.classify_checks(
            [{"id": 1, "name": "application", "head_sha": SHA2, "status": "completed",
              "conclusion": "success", "app": {"slug": "github-actions"}}],
            expected_names=["application"], head_sha=SHA)
        self.assertEqual(result["state"], "failed")

    def test_missing_sha_or_app_cannot_pass(self):
        missing_sha = maintenance.classify_checks(
            [{"id": 1, "name": "application", "status": "completed",
              "conclusion": "success", "app": {"slug": "github-actions"}}],
            expected_names=["application"], head_sha=SHA)
        self.assertEqual(missing_sha["state"], "failed")
        missing_app = maintenance.classify_checks(
            [{"id": 1, "name": "application", "head_sha": SHA, "status": "completed",
              "conclusion": "success"}],
            expected_names=["application"], head_sha=SHA)
        self.assertEqual(missing_app["state"], "failed")

    def test_latest_id_wins(self):
        result = maintenance.classify_checks(
            [
                {"id": 1, "name": "application", "head_sha": SHA, "status": "completed",
                 "conclusion": "failure", "app": {"slug": "github-actions"}},
                {"id": 9, "name": "application", "head_sha": SHA, "status": "completed",
                 "conclusion": "success", "app": {"slug": "github-actions"}},
            ],
            expected_names=["application"], head_sha=SHA)
        self.assertEqual(result["state"], "ready")

    def test_expected_workflow_identity_is_required(self):
        checks = [{
            "id": 1, "name": "application", "head_sha": SHA, "status": "completed",
            "conclusion": "success", "app": {"slug": "github-actions"},
            "html_url": "https://github.com/uesu/News-Express/actions/runs/2/job/1",
        }]
        missing = maintenance.classify_checks(
            checks, expected_names=["application"], head_sha=SHA,
            expected_workflow="CI — syntax + offline smoke test")
        self.assertEqual(missing["state"], "failed")
        self.assertIn("workflow", missing["reason"])
        wrong = maintenance.classify_checks(
            checks, expected_names=["application"], head_sha=SHA,
            expected_workflow="CI — syntax + offline smoke test",
            workflow_runs=[{"id": 1, "name": "other", "head_sha": SHA,
                            "path": ".github/workflows/ci.yml",
                            "status": "completed", "conclusion": "success"}],
        )
        self.assertEqual(wrong["state"], "failed")
        other_run = maintenance.classify_checks(
            [{
                "id": 1, "name": "application", "head_sha": SHA, "status": "completed",
                "conclusion": "success", "app": {"slug": "github-actions"},
                "html_url": "https://github.com/uesu/News-Express/actions/runs/999/job/1",
            }],
            expected_names=["application"], head_sha=SHA,
            expected_workflow="CI — syntax + offline smoke test",
            expected_workflow_path=".github/workflows/ci.yml",
            workflow_runs=[{"id": 2, "name": "CI — syntax + offline smoke test",
                            "head_sha": SHA, "path": ".github/workflows/ci.yml",
                            "status": "completed", "conclusion": "success"}],
            workflow_jobs=[{
                "id": 10, "name": "application", "run_id": 2, "head_sha": SHA,
                "status": "completed", "conclusion": "success",
            }],
        )
        self.assertEqual(other_run["state"], "failed")
        missing_wf_sha = maintenance.classify_checks(
            checks, expected_names=["application"], head_sha=SHA,
            expected_workflow="CI — syntax + offline smoke test",
            workflow_runs=[{"id": 2, "name": "CI — syntax + offline smoke test",
                            "status": "completed", "conclusion": "success"}],
        )
        self.assertEqual(missing_wf_sha["state"], "failed")
        missing_jobs = maintenance.classify_checks(
            checks, expected_names=["application"], head_sha=SHA,
            expected_workflow="CI — syntax + offline smoke test",
            expected_workflow_path=".github/workflows/ci.yml",
            workflow_runs=[{"id": 2, "name": "CI — syntax + offline smoke test",
                            "head_sha": SHA, "path": ".github/workflows/ci.yml",
                            "status": "completed", "conclusion": "success"}],
        )
        self.assertEqual(missing_jobs["state"], "failed")
        self.assertEqual(missing_jobs["reason"], "missing-workflow-jobs")
        ready = maintenance.classify_checks(
            checks, expected_names=["application"], head_sha=SHA,
            expected_workflow="CI — syntax + offline smoke test",
            expected_workflow_path=".github/workflows/ci.yml",
            workflow_runs=[{"id": 2, "name": "CI — syntax + offline smoke test",
                            "head_sha": SHA, "path": ".github/workflows/ci.yml",
                            "status": "completed", "conclusion": "success"}],
            workflow_jobs=[{
                "id": 10, "name": "application", "run_id": 2, "head_sha": SHA,
                "status": "completed", "conclusion": "success",
            }],
        )
        self.assertEqual(ready["state"], "ready")


class MergeDecisionTests(unittest.TestCase):
    def test_happy_path_merges(self):
        decision = maintenance.decide_merge(_snapshot())
        self.assertEqual(decision.action, "merge")
        self.assertEqual(decision.merge_method, "squash")

    def test_missing_field_fails_closed(self):
        snap = _snapshot()
        del snap["checks"]
        decision = maintenance.decide_merge(snap)
        self.assertEqual(decision.action, "fail")
        self.assertIn("missing-field", decision.reason)

    def test_hold_label_and_changes_requested(self):
        hold = maintenance.decide_merge(_snapshot(pull_request=_pr(labels=[{"name": "hold"}])))
        self.assertEqual(hold.action, "defer")
        changes = maintenance.decide_merge(_snapshot(reviews=[{"state": "CHANGES_REQUESTED"}]))
        self.assertEqual(changes.action, "defer")
        superseded = maintenance.decide_merge(_snapshot(reviews=[
            {"id": 1, "state": "CHANGES_REQUESTED", "user": {"login": "reviewer"}},
            {"id": 2, "state": "APPROVED", "user": {"login": "reviewer"}},
        ]))
        self.assertEqual(superseded.action, "merge")
        commented = maintenance.decide_merge(_snapshot(reviews=[
            {"id": 1, "state": "CHANGES_REQUESTED", "user": {"login": "reviewer"}},
            {"id": 2, "state": "COMMENTED", "user": {"login": "reviewer"}},
        ]))
        self.assertEqual(commented.action, "defer")
        self.assertEqual(commented.reason, "changes-requested")
        pending = maintenance.decide_merge(_snapshot(reviews=[
            {"id": 1, "state": "CHANGES_REQUESTED", "user": {"login": "reviewer"}},
            {"id": 2, "state": "PENDING", "user": {"login": "reviewer"}},
        ]))
        self.assertEqual(pending.action, "defer")
        self.assertEqual(pending.reason, "changes-requested")
        dismissed = maintenance.decide_merge(_snapshot(reviews=[
            {"id": 1, "state": "CHANGES_REQUESTED", "user": {"login": "reviewer"}},
            {"id": 2, "state": "DISMISSED", "user": {"login": "reviewer"}},
        ]))
        self.assertEqual(dismissed.action, "merge")
        two_reviewers = maintenance.decide_merge(_snapshot(reviews=[
            {"id": 1, "state": "CHANGES_REQUESTED", "user": {"login": "alex"}},
            {"id": 2, "state": "APPROVED", "user": {"login": "blair"}},
        ]))
        self.assertEqual(two_reviewers.action, "defer")
        self.assertEqual(two_reviewers.reason, "changes-requested")

    def test_untrusted_updater_and_head_change(self):
        human = maintenance.decide_merge(_snapshot(pull_request=_pr(login="alice")))
        self.assertEqual(human.action, "defer")
        moved = maintenance.decide_merge(_snapshot(head_sha=SHA2))
        self.assertEqual(moved.action, "fail")

    def test_python_bump_pat_proposer_is_not_commit_author_alone(self):
        identities = _snapshot()["policy"]["updater_identities"]
        # github-actions[bot] on a random branch is not a runtime bump.
        stray = maintenance.trusted_updater(
            _pr(login="github-actions[bot]", ref="feature/other"), identities)
        self.assertIsNone(stray)
        # PAT opened the PR; commits are the bot's; branch prefix required.
        pat = maintenance.trusted_updater(
            _pr(login="news-express-bump", ref="chore/python-3.14.9"),
            identities,
            commits=[{"author": {"login": "github-actions[bot]"},
                      "committer": {"login": "github-actions[bot]"}}],
        )
        self.assertEqual(pat, "python_bump")
        # Commit author alone, without the prefix, is still untrusted.
        author_only = maintenance.trusted_updater(
            _pr(login="news-express-bump", ref="feature/pin"),
            identities,
            commits=[{"author": {"login": "github-actions[bot]"}}],
        )
        self.assertIsNone(author_only)

    def test_dependabot_allowlist_is_not_the_pr_file_list(self):
        snap = _snapshot(files=[
            {"filename": "testing area/reddit_main_v3.py", "patch": "+x\n"},
        ])
        decision = maintenance.decide_merge(snap)
        self.assertNotEqual(decision.action, "merge")

    def test_auto_merge_flag_must_be_exact_yes(self):
        for value in ("Yes", "true", "1", "on", ""):
            decision = maintenance.decide_merge(_snapshot(variables={"AUTO_MERGE_DEPENDABOT": value}))
            self.assertEqual(decision.action, "defer", value)

    def test_python_bump_rejects_extra_paths(self):
        pr = _pr(login="github-actions[bot]", ref="chore/python-3.14.9")
        snap = _snapshot(
            pull_request=pr,
            files=[{"filename": ".python-version", "patch": "-3.14.8\n+3.14.9\n"},
                   {"filename": "README.md", "patch": "+x\n"}],
            variables={"AUTO_MERGE_PYTHON_BUMP": "yes"},
            risk={"risk": "routine", "auto_eligible": True},
        )
        decision = maintenance.decide_merge(snap)
        self.assertEqual(decision.action, "review-required")

    def test_workflow_policy_change_is_not_routine(self):
        files = [{
            "filename": ".github/workflows/ci.yml",
            "patch": "+      timeout-minutes: 99\n",
        }]
        snap = _snapshot(files=files)
        decision = maintenance.decide_merge(snap)
        self.assertNotEqual(decision.action, "merge")

    def test_fixture_cli_refuses_live_fallback(self):
        with self.assertRaises(SystemExit):
            maintenance.main(["decide"])
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "snap.json"
            fixture.write_text("{}\n", encoding="utf-8")
            self.assertEqual(maintenance.main(["decide", "--fixture", str(fixture)]), 1)
            self.assertEqual(
                maintenance.main(["decide", "--fixture", str(fixture), "--apply"]), 2)


class PythonBumpAdapterTests(unittest.TestCase):
    def test_write_pin_rewrites_only_the_pin_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pin = root / ".python-version"
            pin.write_text("3.14.8\n", encoding="utf-8")
            extra = root / "README.md"
            extra.write_text("stay\n", encoding="utf-8")
            profile = ROOT / ".github" / "maintenance.json"
            code = python_version_bump.main([
                "--write-pin", "--candidate", "3.14.9",
                "--root", str(root), "--profile", str(profile),
            ])
            self.assertEqual(code, 0)
            self.assertEqual(pin.read_text(encoding="utf-8"), "3.14.9\n")
            self.assertEqual(extra.read_text(encoding="utf-8"), "stay\n")

    def test_missing_docs_are_ok_for_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".python-version").write_text("3.14.8\n", encoding="utf-8")
            fixture = Path(tmp) / "fix.json"
            fixture.write_text(json.dumps({
                "current": "3.14.8",
                "manifest": [{
                    "version": "3.14.8",
                    "stable": True,
                    "files": [{"platform": "linux", "arch": "x64"}],
                }],
            }), encoding="utf-8")
            code = python_version_bump.main([
                "--fixture", str(fixture),
                "--root", str(root),
                "--profile", str(ROOT / ".github" / "maintenance.json"),
            ])
            self.assertEqual(code, 0)

    def test_live_without_fixture_or_manifest_refuses(self):
        self.assertEqual(python_version_bump.main([]), 2)


class CiRegistryTests(unittest.TestCase):
    def test_unregistered_test_file_is_rejected(self):
        import ci as ci_mod
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_orphan.py").write_text("print(1)\n", encoding="utf-8")
            profile = {"test_commands": {"application": [["python", "tests/test_smoke.py"]]}}
            with self.assertRaises(SystemExit) as caught:
                ci_mod.ensure_all_tests_registered(root, profile)
            self.assertIn("unregistered", str(caught.exception))

    def test_final_gate_fail_closed(self):
        import ci as ci_mod
        self.assertEqual(ci_mod.final_gate({"application": 0, "maintenance": 1}), 1)
        self.assertEqual(ci_mod.final_gate({"application": 0, "maintenance": 0}), 0)

    def test_actionlint_skip_and_missing_pin_are_not_success(self):
        import ci as ci_mod
        self.assertEqual(ci_mod.maybe_run_actionlint(ROOT, {}), 1)
        previous = os.environ.get("SKIP_ACTIONLINT")
        os.environ["SKIP_ACTIONLINT"] = "1"
        try:
            self.assertEqual(
                ci_mod.maybe_run_actionlint(ROOT, {"url": "https://example.test/x", "sha256": "abc"}),
                1,
            )
        finally:
            if previous is None:
                os.environ.pop("SKIP_ACTIONLINT", None)
            else:
                os.environ["SKIP_ACTIONLINT"] = previous

    def test_compile_header_normalizes_patch_python(self):
        text = "# This file is autogenerated by pip-compile with Python 3.14.8\n"
        self.assertIn(
            "with Python 3.14\n",
            maintenance.normalize_compile_header(text),
        )

    def test_lock_header_only_python_patch_is_equivalent(self):
        before = (
            "# This file is autogenerated by pip-compile with Python 3.14.8\n"
            "aiohttp==3.14.5 \\\n    --hash=sha256:aaa\n"
        )
        after = (
            "# This file is autogenerated by pip-compile with Python 3.14\n"
            "aiohttp==3.14.5 \\\n    --hash=sha256:aaa\n"
        )
        self.assertEqual(
            maintenance.normalize_compile_header(before),
            maintenance.normalize_compile_header(after),
        )

    def test_lock_constraint_marker_index_without_pin_change_must_differ(self):
        header = "# This file is autogenerated by pip-compile with Python 3.14.8\n"
        pin = "aiohttp==3.14.5 \\\n    --hash=sha256:aaa\n"
        base = header + pin
        variants = [
            header + "-c constraints.txt\n" + pin,
            header + "aiohttp==3.14.5 ; python_version >= '3.14' \\\n    --hash=sha256:aaa\n",
            header + "--index-url https://example.test/simple\n" + pin,
            header + "aiohttp==3.14.5 \\\n    --hash=sha256:aaa\n    # via otherpkg\n",
        ]
        normalized = maintenance.normalize_compile_header(base)
        for other in variants:
            self.assertNotEqual(normalized, maintenance.normalize_compile_header(other))


class RequirementPolicyTests(unittest.TestCase):
    def test_extra_index_with_pin_is_review_required(self):
        files = [{
            "filename": "requirements.txt",
            "patch": (
                "-aiohttp==3.14.5\n+aiohttp==3.14.6\n"
                "+--extra-index-url https://untrusted.example/simple\n"
            ),
        }]
        risk = maintenance.snapshot_risk_from_files(files, "dependabot")
        self.assertEqual(risk["risk"], "review-required")
        self.assertFalse(risk["auto_eligible"])
        self.assertGreaterEqual(risk["members"], 2)

    def test_marker_constraint_extras_url_and_unparsed_are_review(self):
        cases = [
            ("-aiohttp==3.14.5\n+aiohttp==3.14.6 ; python_version >= \"3.10\"\n",
             "environment-marker"),
            ("-aiohttp==3.14.5\n+aiohttp==3.14.6\n+-c constraints.txt\n",
             "constraint-file"),
            ("-aiohttp==3.14.5\n+aiohttp[speedups]==3.14.6\n",
             "extras-change"),
            ("-aiohttp==3.14.5\n+https://github.com/foo/bar/archive/x.zip\n",
             "direct-or-vcs-url"),
            ("-aiohttp==3.14.5\n+git+https://github.com/foo/bar.git#egg=aiohttp\n",
             "direct-or-vcs-url"),
            ("-aiohttp==3.14.5\n+not a requirement line!!!\n",
             "unparsed-requirement-line"),
            ("+--index-url https://pypi.org/simple\n",
             "unexpected-index-or-source"),
        ]
        for patch, reason in cases:
            risk = maintenance.snapshot_risk_from_files(
                [{"filename": "requirements.txt", "patch": patch}], "dependabot")
            self.assertEqual(risk["risk"], "review-required", reason)
            self.assertFalse(risk["auto_eligible"], reason)
            blob = json.dumps(risk)
            self.assertIn(reason, blob)

    def test_metadata_cannot_override_file_risk(self):
        snap = _snapshot(
            files=[{
                "filename": "requirements.txt",
                "patch": (
                    "-aiohttp==3.14.5\n+aiohttp==3.14.6\n"
                    "+--extra-index-url https://untrusted.example/simple\n"
                ),
            }],
            risk={"risk": "routine", "auto_eligible": True, "reason": "package-patch-or-minor"},
        )
        decision = maintenance.decide_merge(snap)
        self.assertEqual(decision.action, "review-required")
        self.assertNotEqual(decision.risk, "routine")


class BoundJobAndPaginationTests(unittest.TestCase):
    def test_missing_security_job_fails(self):
        checks = [
            {
                "id": 1, "name": "application", "head_sha": SHA, "status": "completed",
                "conclusion": "success", "app": {"slug": "github-actions"},
                "html_url": "https://github.com/uesu/News-Express/actions/runs/2/job/1",
            },
            {
                "id": 2, "name": "workflow-security", "head_sha": SHA, "status": "completed",
                "conclusion": "success", "app": {"slug": "github-actions"},
                "html_url": "https://github.com/uesu/News-Express/actions/runs/2/job/2",
            },
        ]
        result = maintenance.classify_checks(
            checks,
            expected_names=["application", "workflow-security"],
            head_sha=SHA,
            expected_workflow="CI — syntax + offline smoke test",
            expected_workflow_path=".github/workflows/ci.yml",
            workflow_runs=[{
                "id": 2, "name": "CI — syntax + offline smoke test",
                "head_sha": SHA, "path": ".github/workflows/ci.yml",
                "status": "completed", "conclusion": "success",
            }],
            workflow_jobs=[{
                "id": 10, "name": "application", "run_id": 2, "head_sha": SHA,
                "status": "completed", "conclusion": "success",
            }],
        )
        self.assertEqual(result["state"], "failed")
        self.assertIn("security", result["reason"])

    def test_legacy_status_cannot_satisfy_expected_workflow(self):
        result = maintenance.classify_checks(
            [],
            expected_names=["application"],
            head_sha=SHA,
            expected_workflow="CI — syntax + offline smoke test",
            expected_workflow_path=".github/workflows/ci.yml",
            workflow_runs=[{
                "id": 2, "name": "CI — syntax + offline smoke test",
                "head_sha": SHA, "path": ".github/workflows/ci.yml",
                "status": "completed", "conclusion": "success",
            }],
            workflow_jobs=[{
                "id": 10, "name": "application", "run_id": 2, "head_sha": SHA,
                "status": "completed", "conclusion": "success",
            }],
            legacy_statuses=[{
                "context": "application", "state": "success", "sha": SHA,
            }],
        )
        self.assertEqual(result["state"], "failed")

    def test_short_page_with_total_count_fails_closed(self):
        calls = {"n": 0}

        def fake_json(url, token, method="GET", body=None):
            calls["n"] += 1
            return 200, {
                "total_count": 250,
                "jobs": [{"id": i, "name": f"job-{i}"} for i in range(50)],
            }

        original = maintenance._github_json
        maintenance._github_json = fake_json
        try:
            status, payload = maintenance._api_pages(
                "https://api.github.com/repos/uesu/News-Express/actions/runs/2/jobs?per_page=100",
                "token",
                max_pages=3,
            )
        finally:
            maintenance._github_json = original
        self.assertEqual(status, 0)
        self.assertEqual(payload.get("message"), "pagination-truncated")

    def test_jobs_pages_collect_until_total(self):
        pages = [
            (200, {"total_count": 2, "jobs": [{"id": 1, "name": "application"}]}),
            (200, {"total_count": 2, "jobs": [{"id": 2, "name": "maintenance"}]}),
        ]

        def fake_json(url, token, method="GET", body=None):
            return pages.pop(0)

        original = maintenance._github_json
        maintenance._github_json = fake_json
        try:
            status, payload = maintenance._api_pages(
                "https://api.github.com/repos/uesu/News-Express/actions/runs/2/jobs?per_page=1",
                "token",
            )
        finally:
            maintenance._github_json = original
        self.assertEqual(status, 200)
        self.assertEqual([j["name"] for j in payload], ["application", "maintenance"])


class LiveAdapterTests(unittest.TestCase):
    def test_truncated_check_pages_fail_closed(self):
        def fake_json(url, token, method="GET", body=None):
            if "/pulls/12" in url and "files" not in url and "reviews" not in url and "commits" not in url:
                return 200, _pr()
            return 200, {}

        def fake_pages(url, token, **_k):
            if "check-runs" in url:
                return 0, {"message": "pagination-truncated", "count": 100, "total": 250}
            return 200, []

        original_json = maintenance._github_json
        original_pages = maintenance._api_pages
        maintenance._github_json = fake_json
        maintenance._api_pages = fake_pages
        try:
            result = maintenance.build_live_snapshot(
                {
                    "repository": {"full_name": "uesu/News-Express", "default_branch": "main"},
                    "pull_request": {"number": 12, "head": {"sha": SHA}},
                },
                "token",
                {"mandatory_check_names": ["application"],
                 "ci_workflow_name": "CI — syntax + offline smoke test",
                 "ci_workflow_path": ".github/workflows/ci.yml"},
            )
        finally:
            maintenance._github_json = original_json
            maintenance._api_pages = original_pages
        self.assertIsInstance(result, maintenance.Decision)
        self.assertEqual(result.action, "fail")
        self.assertIn("checks-api", result.reason)

    def test_extra_index_files_are_review_required_in_snapshot(self):
        def fake_json(url, token, method="GET", body=None):
            if "/pulls/12" in url and "files" not in url and "reviews" not in url and "commits" not in url:
                return 200, _pr()
            return 200, {}

        def fake_pages(url, token, **_k):
            if "check-runs" in url:
                return 200, [{
                    "id": 1, "name": "application", "head_sha": SHA, "status": "completed",
                    "conclusion": "success", "app": {"slug": "github-actions"},
                    "html_url": "https://github.com/uesu/News-Express/actions/runs/2/job/1",
                }]
            if "/files" in url:
                return 200, [{
                    "filename": "requirements.txt",
                    "patch": (
                        "-aiohttp==3.14.5\n+aiohttp==3.14.6\n"
                        "+--extra-index-url https://untrusted.example/simple\n"
                    ),
                }]
            if "/reviews" in url:
                return 200, []
            if "/statuses" in url:
                return 200, []
            if "/jobs" in url:
                return 200, [{
                    "id": 10, "name": "application", "run_id": 2, "head_sha": SHA,
                    "status": "completed", "conclusion": "success",
                }]
            if "actions/runs" in url:
                return 200, [{
                    "id": 2, "name": "CI — syntax + offline smoke test",
                    "head_sha": SHA, "path": ".github/workflows/ci.yml",
                    "status": "completed", "conclusion": "success",
                }]
            if "/commits" in url:
                return 200, [{"author": {"login": "dependabot[bot]"}}]
            return 200, []

        original_json = maintenance._github_json
        original_pages = maintenance._api_pages
        maintenance._github_json = fake_json
        maintenance._api_pages = fake_pages
        try:
            snapshot = maintenance.build_live_snapshot(
                {
                    "repository": {"full_name": "uesu/News-Express", "default_branch": "main"},
                    "pull_request": {"number": 12, "head": {"sha": SHA}},
                },
                "token",
                {
                    "mandatory_check_names": ["application"],
                    "ci_workflow_name": "CI — syntax + offline smoke test",
                    "ci_workflow_path": ".github/workflows/ci.yml",
                    "updater_identities": {
                        "dependabot": {"login": "dependabot[bot]", "auto_merge_var": "AUTO_MERGE_DEPENDABOT"},
                    },
                    "dependabot_allowed_files": ["requirements.txt"],
                },
            )
        finally:
            maintenance._github_json = original_json
            maintenance._api_pages = original_pages
        self.assertIsInstance(snapshot, dict)
        self.assertEqual(snapshot["risk"]["risk"], "review-required")
        self.assertFalse(snapshot["risk"]["auto_eligible"])
        self.assertGreaterEqual(snapshot["risk"]["members"], 2)
        self.assertTrue(snapshot.get("workflow_jobs"))
        decision = maintenance.decide_merge(snapshot)
        self.assertEqual(decision.action, "review-required")


if __name__ == "__main__":
    unittest.main()
