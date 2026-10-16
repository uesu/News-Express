"""Pin, lock, workflow, and documentation-free production contract."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".github" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import maintenance  # noqa: E402

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - CI installs PyYAML via requirements-dev
    yaml = None

PIN = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class PinAndLockTests(unittest.TestCase):
    def test_exact_pin(self):
        self.assertEqual(PIN, "3.14.8")
        self.assertRegex(PIN, r"^\d+\.\d+\.\d+$")

    def test_hashed_locks_exist(self):
        runtime = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        self.assertIn(" --hash=", runtime)
        self.assertIn(" --hash=", dev)
        self.assertGreater(runtime.count("--hash="), 5)
        self.assertTrue("pip==" in runtime or "pip==" in dev)

    def test_no_actions_lockfile(self):
        self.assertFalse((ROOT / ".github" / "workflows" / "actions.lock").exists())
        for path in (ROOT / ".github" / "workflows").glob("*.yml"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("actions.lock", text)
            self.assertNotIn("gh-actions-lock", text)


class WorkflowContractTests(unittest.TestCase):
    def _text(self, name: str) -> str:
        return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")

    def test_ci_permissions_and_groups(self):
        text = self._text("ci.yml")
        self.assertIn("contents: read", text)
        self.assertNotIn("pull_request_target", text)
        self.assertGreaterEqual(text.count("timeout-minutes:"), 4)
        self.assertIn("python-version-file: .python-version", text)
        self.assertIn("--require-hashes", text)
        self.assertIn("--only-binary=:all:", text)
        self.assertIn("maintenance-ci", text)
        if yaml is not None:
            doc = yaml.safe_load(text)
            self.assertEqual(doc.get("permissions"), {"contents": "read"})

    def test_monitors_keep_dispatch_and_no_native_schedule(self):
        for name in ("reddit_monitor.yml", "twitter_monitor.yml"):
            text = self._text(name)
            self.assertIn("workflow_dispatch:", text)
            self.assertIn("cancel-in-progress: false", text)
            self.assertIn("python-version-file: .python-version", text)
            self.assertIn("render_run_summary.py", text)
            self.assertNotIn("count_matches()", text)
            self.assertIn("write_persist", text)

    def test_merge_controller_trusted_checkout(self):
        text = self._text("maintenance_merge.yml")
        self.assertIn("contents: write", text)
        self.assertIn("default_branch", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("apply-live --apply-live", text)
        self.assertNotIn("ref: ${{ github.event.pull_request.head", text)
        self.assertFalse((ROOT / ".github" / "workflows" / "dependabot_auto_merge.yml").exists())

    def test_python_bump_no_self_merge(self):
        text = self._text("python_version_bump.yml")
        self.assertIn("BUMP_PAT", text)
        self.assertIn("secrets.BUMP_PAT", text)
        self.assertIn("configuration error, not a GITHUB_TOKEN fallback", text)
        self.assertIn("wheels == 'yes'", text)
        self.assertNotIn("gh pr merge", text)
        self.assertGreaterEqual(text.count("--group lock-consistency"), 2)
        self.assertGreaterEqual(text.count("--group workflow-security"), 2)
        self.assertIn("--emit-validation", text)
        self.assertIn("--emit-publication", text)
        self.assertIn('} >> "$GITHUB_OUTPUT"', text)
        self.assertIn("COMMIT_IDENTITY:", text)
        self.assertNotIn('--commit-identity "github-actions[bot]"', text)

    def test_action_pins_are_shas(self):
        for path in (ROOT / ".github" / "workflows").glob("*.yml"):
            for match in re.finditer(r"uses:\s*(\S+?)@(\S+)", path.read_text(encoding="utf-8")):
                ref = match.group(2).split("#", 1)[0].strip()
                self.assertTrue(SHA_RE.fullmatch(ref.lower()), f"{path.name}: {match.group(0)}")


class ProductionCopyTests(unittest.TestCase):
    def test_runtime_files_exist_and_docs_are_optional(self):
        profile = maintenance.load_profile()
        for rel in profile.get("runtime_files") or []:
            self.assertTrue((ROOT / rel).exists(), rel)
        for rel in profile.get("optional_docs") or []:
            self.assertTrue((ROOT / rel).exists(), rel)
        excluded = set(profile.get("production_copy_exclude") or [])
        self.assertIn("README.md", excluded)
        self.assertIn("docs", excluded)
        self.assertIn("posted_reddit.json", excluded)
        self.assertIn("posted_tweets.json", excluded)

    def test_both_engines_and_monitors_are_runtime_files(self):
        profile = maintenance.load_profile()
        runtime = set(profile.get("runtime_files") or [])
        excluded = set(profile.get("production_copy_exclude") or [])
        for rel in (
            "testing area/reddit_main_v3.py",
            "testing area/twitter_v3.py",
            ".github/workflows/reddit_monitor.yml",
            ".github/workflows/twitter_monitor.yml",
            ".github/scripts/maintenance.py",
            ".github/scripts/maintenance_common.py",
            ".github/scripts/ci.py",
            ".python-version",
            "requirements.txt",
            "requirements-dev.txt",
        ):
            self.assertIn(rel, runtime)
            self.assertNotIn(rel, excluded)
        for cache in (
            "posted_reddit.json", "posted_tweets.json",
            "pending_reddit.json", "posted_messages.json", "proxy_health.json",
        ):
            self.assertIn(cache, excluded)
            self.assertNotIn(cache, runtime)
        self.assertNotIn("NEWS_EXPRESS_UPDATE.md", runtime)
        self.assertNotIn("docs/COPY_MANIFEST.md", runtime)
        self.assertNotIn("docs/ACCEPTANCE_COVERAGE.md", runtime)
        self.assertNotIn("docs/proposal_head_hashes.json", runtime)
        self.assertTrue((ROOT / "docs" / "COPY_MANIFEST.md").is_file())
        self.assertTrue((ROOT / "docs" / "ACCEPTANCE_COVERAGE.md").is_file())
        self.assertTrue((ROOT / "docs" / "proposal_head_hashes.json").is_file())

    def test_copy_manifest_does_not_claim_parity_or_identical_helpers(self):
        text = (ROOT / "docs" / "COPY_MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("not equivalent copies", text)
        self.assertIn("not fully aligned", text)
        self.assertIn("open acceptance item", text)
        self.assertIn("inventory, **not** completion of the requirement", text)
        self.assertIn("be4bacaa0e4a1688517549c99915d93d0227024e", text)
        self.assertIn("d123c0d7028061771e3b1789dd9414fed82c06f8", text)
        self.assertIn("26b84ff455ac5675476a55fde357dd63387627ad", text)
        self.assertIn("62a9c30d624ac9717ad3ce11ab380897b03af379", text)
        self.assertIn("171925850552", text)
        self.assertIn("5f0435c56cd7", text)
        self.assertIn("ed7dd1ef5e52", text)
        self.assertIn("766548226b01", text)
        self.assertIn("082aa9a2e4dc", text)
        self.assertIn("c7e02d9531d0", text)
        self.assertIn("No maintainer-approved exception has been granted", text)
        self.assertIn("do **not** claim the helpers are identical", text)
        self.assertIn("not** approved for blind adoption", text)
        self.assertIn("maintenance_common.py", text)
        self.assertNotIn("After both implementation PRs are accepted", text)
        coverage = (ROOT / "docs" / "ACCEPTANCE_COVERAGE.md").read_text(encoding="utf-8")
        self.assertIn("not production parity", coverage)
        self.assertIn("Local 3.11.2 is not the gate", coverage)
        self.assertIn("38837001161", coverage)
        self.assertIn("38855237517", coverage)
        self.assertIn("Helper-only fixtures", coverage)

    def test_news_helper_bytes_match_frozen_proposal_hashes(self):
        artifact = json.loads(
            (ROOT / "docs" / "proposal_head_hashes.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            artifact["heads"]["news"]["ancestor_implementation_bytes"],
            "be4bacaa0e4a1688517549c99915d93d0227024e",
        )
        self.assertIn("cannot embed its own final self-hash", artifact["heads"]["news"]["note"])
        self.assertIn("not approved for blind adoption", artifact["heads"]["news"]["note"])
        self.assertEqual(
            artifact["heads"]["reddit"]["sha"],
            "d123c0d7028061771e3b1789dd9414fed82c06f8",
        )
        self.assertEqual(
            artifact["heads"]["twitter"]["sha"],
            "26b84ff455ac5675476a55fde357dd63387627ad",
        )
        helpers = (
            ".github/scripts/ci.py",
            ".github/scripts/maintenance.py",
            ".github/scripts/maintenance_common.py",
            ".github/scripts/python_version_bump.py",
            ".github/scripts/render_run_summary.py",
            "testing area/reddit_main_v3.py",
            "testing area/twitter_v3.py",
            "requirements.txt",
            ".python-version",
        )
        files = artifact["files"]
        for rel in helpers:
            digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            self.assertEqual(digest, files[rel]["news"], rel)

    def test_gitignore_covers_reports(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".reports/", text)
        self.assertIn("run-report", text)


if __name__ == "__main__":
    unittest.main()
