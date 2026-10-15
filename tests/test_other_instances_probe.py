"""Offline only: fixed fleet, excluded hosts, account scoping, rate-limit stop."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

SCRIPT = Path(__file__).resolve().parents[1] / '.github/scripts/probe_other_instances.py'
spec = importlib.util.spec_from_file_location('other_probe', SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class FleetTests(unittest.TestCase):
    def test_fixed_fleet_counts_and_exclusions(self):
        self.assertEqual(len(probe.NITTER_HOSTS), 17)
        self.assertEqual(len(probe.REDDIT_HOSTS), 6)
        self.assertEqual(len(set(probe.HOSTS)), 23)
        self.assertFalse(set(probe.HOSTS) & probe.EXCLUDED)
        for host in probe.EXCLUDED | {'unreviewed.example'}:
            with self.assertRaises(ValueError): probe.endpoints_for(host, 'rss')

    def test_fixed_routes_cover_eight_handles_and_six_subreddits(self):
        total = 0
        for host in probe.HOSTS:
            routes = ['rss'] if host in probe.NITTER_HOSTS else probe.ROUTES
            for route in routes:
                endpoints = probe.endpoints_for(host, route)
                self.assertEqual(len(endpoints), 8 if host in probe.NITTER_HOSTS else 6)
                self.assertLessEqual(len(endpoints) + 1, 10)
                for url, kind, pristine in endpoints.values():
                    total += 1
                    self.assertEqual(urlsplit(url).hostname, host)
                    self.assertEqual(urlsplit(url).scheme, 'https')
                    self.assertNotIn('token', url)
                    if host in probe.NITTER_HOSTS:
                        self.assertEqual(kind, 'twitter_feed')
                        self.assertTrue(url.endswith('/rss'))
                    elif route == 'rss': self.assertTrue(url.endswith('/new/.rss'))
                    elif route == 'pristine': self.assertTrue(pristine)
        self.assertEqual(total, 244)

    def test_reject_nitter_html_routes(self):
        with self.assertRaises(ValueError): probe.endpoints_for(probe.NITTER_HOSTS[0], 'root')

    def test_account_scoping_for_every_union_handle(self):
        for account in probe.ACCOUNTS:
            body = f'<rss><channel><item><link>https://example.org/{account.lower()}/status/123456789012345</link></item></channel></rss>'.encode()
            self.assertEqual(probe.base.inspect_body(body, 'twitter_feed', account=account)['matching_entries'], 1)
            self.assertEqual(probe.base.inspect_body(body, 'twitter_feed', account='wrong')['matching_entries'], 0)

    def test_fetch_uses_account_in_fixed_request(self):
        host = probe.NITTER_HOSTS[0]
        class Response:
            code = 200
            headers = {'Content-Type': 'application/rss+xml'}
            def geturl(self): return f'https://{host}/ZZZ_EN/rss'
            def read(self, n): return b'<rss><channel><item><link>/ZZZ_EN/status/123456789</link></item></channel></rss>'
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class Opener:
            def open(self, *args, **kwargs): return Response()
        with patch.object(probe.base, 'ENDPOINTS', probe.endpoints_for(host, 'rss')), patch.object(probe.base, 'build_opener', return_value=Opener()):
            result = probe.base.fetch_endpoint('ZZZ_EN')
        self.assertEqual(result['account'], 'ZZZ_EN')
        self.assertTrue(result['candidate_response'])

    def test_429_stops_current_and_later_route_steps(self):
        host = probe.REDDIT_HOSTS[0]
        with tempfile.TemporaryDirectory() as directory:
            cooldown = Path(directory) / 'cooldown.json'
            with patch.object(probe, 'probe_bounded', return_value={'http_status': 429, 'candidate_response': False}) as fetch, patch.object(probe.time, 'sleep'):
                rss = probe.collect(host, 'rss', cooldown)
                root = probe.collect(host, 'root', cooldown)
                self.assertEqual(fetch.call_count, 1)
            self.assertEqual(rss[0]['http_status'], 429)
            self.assertTrue(all(r['body_class'] == 'not_requested_after_429' for r in rss[1:] + root))
            self.assertEqual(json.loads(cooldown.read_text())['host'], host)

    def test_403_is_an_observation_not_a_rate_limit_skip(self):
        host = probe.NITTER_HOSTS[0]
        with patch.object(probe, 'probe_bounded', side_effect=lambda h, r, n: {'endpoint': n, 'http_status': 403, 'candidate_response': False}) as fetch, patch.object(probe.time, 'sleep') as pause:
            results = probe.collect(host, 'rss', None)
        self.assertEqual(fetch.call_count, 8)
        self.assertEqual(pause.call_count, 7)
        self.assertTrue(all(r['http_status'] == 403 for r in results))

    def test_deadline_and_worker_errors(self):
        args = (probe.NITTER_HOSTS[0], 'rss', 'TYPEII_EN')
        with patch.object(probe.subprocess, 'run', side_effect=subprocess.TimeoutExpired('probe', 20)):
            self.assertEqual(probe.probe_bounded(*args)['body_class'], 'total_deadline_exceeded')
        for code, text, expected in [(1, '', 'probe_worker_failed'), (0, 'not JSON', 'invalid_worker_output')]:
            with patch.object(probe.subprocess, 'run', return_value=subprocess.CompletedProcess([], code, text, '')):
                self.assertEqual(probe.probe_bounded(*args)['body_class'], expected)

    def test_workflow_only_runs_new_fixed_fleet_without_secrets(self):
        workflow = (SCRIPT.parents[1] / 'workflows/freedit_probe.yml').read_text()
        matrix_hosts = [line.split(': ', 1)[1] for line in workflow.splitlines() if line.strip().startswith('- host: ')]
        self.assertEqual(matrix_hosts, list(probe.HOSTS))
        self.assertNotIn('${{ secrets.', workflow)
        self.assertNotIn('--suite ', workflow)
        self.assertIn('max-parallel: 4', workflow)
        self.assertIn('fail-fast: false', workflow)
        self.assertEqual(workflow.count('--cooldown-file '), 3)
        self.assertIn('branches: [arena/c45edf9b-news-express]', workflow)


if __name__ == '__main__':
    unittest.main(verbosity=2)
