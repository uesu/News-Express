"""Offline tests only; never contacts public mirrors or runs a monitor."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

SCRIPT = Path(__file__).resolve().parents[1] / '.github/scripts/probe_freedit.py'
spec = importlib.util.spec_from_file_location('freedit_probe', SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class BodyTests(unittest.TestCase):
    def test_200_challenge_is_not_rss(self):
        r = probe.inspect_body(b'<html>__goaway_challenge</html>', 'reddit_feed')
        self.assertEqual(r['body_class'], 'non_feed_xml')
        self.assertIn('goaway_challenge', r['markers'])
        self.assertEqual(r['matching_entries'], 0)

    def test_redlib_upstream_error_not_mistaken_for_feed(self):
        r = probe.inspect_body(b'<html>Reddit error 400: Bad Request</html>', 'reddit_feed')
        self.assertEqual(r['matching_entries'], 0)
        self.assertIn('reddit_error', r['markers'])
        self.assertIn('bad_request', r['markers'])

    def test_rss_entry_with_expected_subreddit_and_date(self):
        xml = b'''<rss><channel><item><link>https://redlib.freedit.eu/r/Genshin_Impact_Leaks/comments/abc123/title/</link>
        <pubDate>Thu, 15 Oct 2026 10:00:00 GMT</pubDate></item></channel></rss>'''
        r = probe.inspect_body(xml, 'reddit_feed')
        self.assertEqual(r['matching_entries'], 1)
        self.assertEqual(r['newest_matching'], [{'id': 'abc123', 'date_utc': '2026-10-15T10:00:00+00:00'}])

    def test_atom_feed_and_date(self):
        xml = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
        <link href="https://www.reddit.com/r/Genshin_Impact_Leaks/comments/abc123/title/"/>
        <updated>2026-10-15T10:00:00Z</updated></entry></feed>'''
        r = probe.inspect_body(xml, 'reddit_feed')
        self.assertEqual(r['matching_entries'], 1)
        self.assertEqual(r['newest_matching'][0]['date_utc'], '2026-10-15T10:00:00+00:00')

    def test_wrong_subreddit_and_link_in_description_do_not_count(self):
        xml = b'''<rss><channel><item><link>https://reddit.com/r/wrong/comments/abc123/t</link>
        <description>https://reddit.com/r/Genshin_Impact_Leaks/comments/abc123/t</description>
        </item></channel></rss>'''
        self.assertEqual(probe.inspect_body(xml, 'reddit_feed')['matching_entries'], 0)

    def test_empty_feed_is_not_approved(self):
        self.assertEqual(probe.inspect_body(b'<rss><channel/></rss>', 'reddit_feed')['body_class'],
                         'feed_without_matching_entries')

    def test_twitter_expected_account(self):
        xml = b'''<rss><channel><item><link>https://nitter.freedit.eu/TYPEII_EN/status/123456789</link></item>
        <item><link>https://x.com/Other/status/987654321</link></item></channel></rss>'''
        r = probe.inspect_body(xml, 'twitter_feed')
        self.assertEqual(r['entries'], 2)
        self.assertEqual(r['matching_entries'], 1)

    def test_xml_dtd_rejected(self):
        xml = b'<!DOCTYPE rss [<!ENTITY a "abc">]><rss><channel>&a;</channel></rss>'
        self.assertEqual(probe.inspect_body(xml, 'reddit_feed')['body_class'], 'non_feed_or_dtd')

    def test_utf16_dtd_rejected_by_parser(self):
        xml = '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE rss [<!ENTITY a "abc">]><rss><channel>&a;</channel></rss>'.encode('utf-16')
        r = probe.inspect_body(xml, 'reddit_feed')
        self.assertEqual(r['matching_entries'], 0)
        self.assertEqual(r['body_class'], 'not_feed_xml')

    def test_html_links_and_visible_age(self):
        html = b'''<a href="/r/Genshin_Impact_Leaks/comments/abc123/title/">Title</a>
        <a href="/r/Genshin_Impact_Leaks/comments/abc123/title/">Comments</a>
        <span class="created">2 hours ago</span>'''
        r = probe.inspect_body(html, 'listing')
        self.assertEqual(r['post_ids_count'], 1)
        self.assertEqual(r['oldest_visible_age_seconds'], 7200)

    def test_html_shell_and_other_sub_not_listing_evidence(self):
        r = probe.inspect_body(b'<html><a href="/r/Other/comments/abc123/t/">Post</a></html>', 'listing')
        self.assertEqual(r['post_ids_count'], 0)
        self.assertEqual(r['body_class'], 'html_without_post_links')

    def test_homepage_not_evidence(self):
        r = probe.inspect_body(b'<html>Welcome</html>', 'home')
        self.assertEqual(r['body_class'], 'homepage_only_not_feed_evidence')

    def test_invalid_date_is_reported_without_age_guess(self):
        xml = b'''<rss><channel><item><link>/TYPEII_EN/status/123</link><pubDate>nonsense</pubDate></item></channel></rss>'''
        self.assertIsNone(probe.inspect_body(xml, 'twitter_feed')['newest_matching'][0]['date_utc'])


class RequestTests(unittest.TestCase):
    def test_exact_requested_urls_and_runtime_alias(self):
        self.assertEqual(probe.request_details('redlib_engine_rss')[0],
                         'https://redlib.freedit.eu/r/Genshin_Impact_Leaks/new/.rss')
        self.assertEqual(probe.request_details('redlib_requested_rss')[0],
                         'https://redlib.freedit.eu/r/Genshin_Impact_Leaks/new.rss?limit=100')
        self.assertEqual(probe.request_details('nitter_requested_rss')[0],
                         'https://nitter.freedit.eu/TYPEII_EN/rss')

    def test_six_game_suites_cover_requested_and_runtime_routes(self):
        self.assertEqual(len(probe.SUBREDDITS), 6)
        urls = []
        for game, sub in probe.SUBREDDITS.items():
            self.assertIn(f'eddrit_{game}_html_new', probe.SUITES[game])
            self.assertEqual(probe.request_details(f'eddrit_{game}_html_new')[0],
                             f'https://eddrit.com/r/{sub}/new')
            self.assertEqual(probe.request_details(f'eddrit_{game}_engine_rss')[0],
                             f'https://eddrit.com/r/{sub}/.rss')
            self.assertEqual(probe.request_details(f'eddrit_{game}_new_rss')[0],
                             f'https://eddrit.com/r/{sub}/new/.rss')
            self.assertEqual(probe.request_details(f'freedit_{game}_html_root')[0],
                             f'https://redlib.freedit.eu/r/{sub}')
            urls.extend(probe.request_details(name)[0] for name in probe.SUITES[game])
        self.assertEqual(len(urls), 25)
        self.assertEqual(len(set(urls)), 25)
        self.assertIn('https://eddrit.com/r/Zenlesszonezeroleaks_/new', urls)
        self.assertIn('https://redlib.freedit.eu/r/Genshin_Impact_Leaks', urls)
        self.assertEqual(len(probe.SUITES['freedit']), 8)

    def test_each_game_parser_scopes_html_and_rss_to_its_own_subreddit(self):
        for sub in probe.SUBREDDITS.values():
            with self.subTest(sub=sub):
                link = f'/r/{sub.lower()}/comments/abc123/t/'
                xml = f'<rss><channel><item><link>{link}</link></item></channel></rss>'.encode()
                html = f'<a href="{link}">Post</a>'.encode()
                self.assertEqual(probe.inspect_body(xml, 'reddit_feed', sub)['matching_entries'], 1)
                self.assertEqual(probe.inspect_body(xml, 'reddit_feed', 'DifferentSub')['matching_entries'], 0)
                self.assertEqual(probe.inspect_body(html, 'listing', sub)['post_ids_count'], 1)
                self.assertEqual(probe.inspect_body(html, 'listing', 'DifferentSub')['post_ids_count'], 0)

    def test_fetch_selects_expected_subreddit_from_fixed_url(self):
        class Response:
            code = 200
            headers = {'Content-Type': 'text/html'}
            def geturl(self): return 'https://eddrit.com/r/Zenlesszonezeroleaks_/new'
            def read(self, n): return b'<a href="/r/Zenlesszonezeroleaks_/comments/abc123/t/">Post</a>'
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class Opener:
            def open(self, *args, **kwargs): return Response()
        with patch.object(probe, 'build_opener', return_value=Opener()):
            r = probe.fetch_endpoint('eddrit_zzz_html_new')
        self.assertEqual(r['subreddit'], 'Zenlesszonezeroleaks_')
        self.assertTrue(r['candidate_response'])

    def test_preserved_six_suites_have_bounded_total_time(self):
        workflow = (SCRIPT.parents[1] / 'workflows/freedit_probe.yml').read_text()
        total_endpoints = 0
        worst_seconds = 0
        for game in probe.SUBREDDITS:
            n = len(probe.SUITES[game])
            self.assertLessEqual(n + 1, 10)  # Include the suite context notice.
            total_endpoints += n
            worst_seconds += n * probe.ENDPOINT_DEADLINE + (n - 1) * probe.PAUSE_SECONDS
        self.assertEqual(total_endpoints, 25)
        self.assertLess(worst_seconds + 30, 10 * 60)  # Checkout/test allowance.

    def test_no_credential_forwarding_even_if_environment_has_tokens(self):
        with patch.dict(os.environ, {'NITTER_RSS_TOKEN': 'DO_NOT_FORWARD', 'REDDIT_FEED_TOKEN': 'DO_NOT_FORWARD'}):
            for name in probe.ENDPOINTS:
                url, headers = probe.request_details(name)
                self.assertNotIn('DO_NOT_FORWARD', json.dumps([url, headers]))
                self.assertNotIn('Authorization', headers)
                self.assertNotIn('Cookie', headers)

    def test_pristine_request_matches_engine_cache_controls(self):
        url, headers = probe.request_details('redlib_pristine_html', fresh_ms=12345)
        self.assertTrue(url.endswith('&_fresh=12345'))
        self.assertEqual(headers['Cache-Control'], 'no-cache, no-store')
        self.assertEqual(headers['Pragma'], 'no-cache')

    def test_redirect_policy_blocks_other_hosts_userinfo_and_downgrades(self):
        handler = probe.SameHostRedirects()
        req = Request('https://redlib.freedit.eu/')
        for dest in ['http://redlib.freedit.eu/', 'https://other.example/',
                     'https://user:pass@redlib.freedit.eu/', 'https://redlib.freedit.eu:444/']:
            with self.subTest(dest=dest), self.assertRaises(HTTPError):
                handler.redirect_request(req, None, 302, 'Found', {}, dest)
        self.assertEqual(handler.redirect_request(req, None, 302, 'Found', {},
                                                 'https://redlib.freedit.eu/new').full_url,
                         'https://redlib.freedit.eu/new')

    def test_total_request_deadline(self):
        with patch.object(probe.subprocess, 'run', side_effect=subprocess.TimeoutExpired('worker', 20)):
            r = probe.probe_bounded('nitter_requested_rss')
        self.assertEqual(r['body_class'], 'total_deadline_exceeded')
        self.assertFalse(r['candidate_response'])

    def test_worker_failure_is_recorded(self):
        with patch.object(probe.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', '')):
            self.assertEqual(probe.probe_bounded('redlib_home')['body_class'], 'probe_worker_failed')

    def test_bad_worker_output_is_recorded(self):
        with patch.object(probe.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'bad json', '')):
            self.assertEqual(probe.probe_bounded('redlib_home')['body_class'], 'invalid_worker_output')

    def test_http_failure_cannot_be_candidate_despite_valid_body(self):
        class Response:
            code = 403
            headers = {'Content-Type': 'application/rss+xml'}
            def geturl(self): return 'https://nitter.freedit.eu/TYPEII_EN/rss'
            def read(self, n): return b'<rss><channel><item><link>/TYPEII_EN/status/123</link></item></channel></rss>'
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class Opener:
            def open(self, *args, **kwargs): return Response()
        with patch.object(probe, 'build_opener', return_value=Opener()):
            r = probe.fetch_endpoint('nitter_requested_rss')
        self.assertEqual(r['matching_entries'], 1)
        self.assertFalse(r['candidate_response'])

    def test_oversize_response_not_parsed(self):
        class Response:
            code = 200
            headers = {}
            def geturl(self): return 'https://nitter.freedit.eu/TYPEII_EN/rss'
            def read(self, n): return b'x' * n
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class Opener:
            def open(self, *args, **kwargs): return Response()
        with patch.object(probe, 'build_opener', return_value=Opener()):
            r = probe.fetch_endpoint('nitter_requested_rss')
        self.assertEqual(r['body_class'], 'oversize_not_parsed')
        self.assertFalse(r['candidate_response'])

    def test_listing_candidate_requires_html_content_type(self):
        class Response:
            code = 200
            headers = {}
            def geturl(self): return 'https://redlib.freedit.eu/r/Genshin_Impact_Leaks/new'
            def read(self, n): return b'<a href="/r/Genshin_Impact_Leaks/comments/abc123/t/">Title</a>'
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class Opener:
            def open(self, *args, **kwargs): return Response()
        for mime, expected in [('text/html; charset=utf-8', True), ('text/plain', False)]:
            Response.headers = {'Content-Type': mime}
            with self.subTest(mime=mime), patch.object(probe, 'build_opener', return_value=Opener()):
                r = probe.fetch_endpoint('redlib_requested_html')
            self.assertEqual(r['candidate_response'], expected)

    def test_feed_success_and_error_marker_candidates(self):
        class Response:
            code = 200
            headers = {'Content-Type': 'application/rss+xml'}
            body = b''
            def geturl(self): return 'https://nitter.freedit.eu/TYPEII_EN/rss'
            def read(self, n): return self.body
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class Opener:
            def open(self, *args, **kwargs): return Response()
        for title, expected in [('Fixture', True), ('enable javascript', False)]:
            Response.body = ('<rss><channel><item><link>/TYPEII_EN/status/123456789</link>'
                             f'<title>{title}</title></item></channel></rss>').encode()
            with self.subTest(title=title), patch.object(probe, 'build_opener', return_value=Opener()):
                self.assertEqual(probe.fetch_endpoint('nitter_requested_rss')['candidate_response'], expected)

    def test_annotations_are_escaped_json_not_remote_commands(self):
        report = {'run_id': '123', 'results': [{'endpoint': 'redlib_home',
                  'cache-control': 'hostile%0A::error::test\nsecond line'}]}
        commands = list(probe.annotation_commands(report))
        self.assertEqual(len(commands), 2)
        self.assertTrue(all(c.startswith('::notice title=Mirror diagnostic result::') for c in commands))
        self.assertNotIn('\n', commands[1])
        self.assertIn('%250A', commands[1])
        self.assertNotIn('results', json.loads(commands[0].split('::', 2)[2]))

    def test_transport_failure_recorded(self):
        class Opener:
            def open(self, *args, **kwargs): raise URLError('fixture refusal')
        with patch.object(probe, 'build_opener', return_value=Opener()):
            self.assertEqual(probe.fetch_endpoint('redlib_home')['transport_error'], 'URLError')

    def test_workflow_branch_scoped_read_only_and_not_a_monitor(self):
        workflow = (SCRIPT.parents[1] / 'workflows/freedit_probe.yml').read_text()
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn('branches: [arena/c45edf9b-news-express]', workflow)
        self.assertIn('paths:', workflow)
        self.assertIn('contents: read', workflow)
        self.assertIn('persist-credentials: false', workflow)
        self.assertIn('timeout-minutes: 10', workflow)
        self.assertNotIn('${{ secrets.', workflow)
        self.assertNotIn('schedule:', workflow)
        self.assertNotIn('git push', workflow)
        self.assertNotIn('reddit_main_v3.py', workflow)
        self.assertNotIn('twitter_v3.py', workflow)


if __name__ == '__main__':
    unittest.main(verbosity=2)
