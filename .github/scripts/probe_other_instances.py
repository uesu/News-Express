#!/usr/bin/env python3
"""Fixed public fleet probe; no monitors, credentials, retries or posting.

Each matrix job owns one host. A 429 stops that host for the rest of the job,
including later route steps. Explicitly excluded hosts cannot be selected.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

BASE_PATH = Path(__file__).with_name('probe_freedit.py')
spec = importlib.util.spec_from_file_location('public_mirror_probe', BASE_PATH)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

PAUSE_SECONDS = 5
ACCOUNTS = ('TYPEII_EN', 'PomPom_HonkaiSR', 'Wuthering_Waves', 'HonkaiNA',
            'Ananta_EN', 'GenshinImpact', 'honkaistarrail', 'ZZZ_EN')
EXCLUDED = {'nitter.cf', 'xitter.cf', 'nitter.freedit.eu', 'redlib.freedit.eu',
            'eddrit.com', 'nitter.miningtcup.me', 'redlib.miningtcup.me'}
NITTER_HOSTS = (
    'nitter.meowing.monster', 'nitter.gravitywell.xyz', 'tw.eir-nya.gay',
    'shitter.thepixora.com', 'nitter.kareem.one', 'xcopy.uk',
    'nitter.netbub.com', 'nitter.jaydenha.uk', 'nitter.click',
    'nitter.tiekoetter.com', 'nitter.xitter.cc', 'nitter.perennialte.ch',
    'nitter.privacydev.net', 'nitter.net', 'xcancel.com', 'x.yuuki.sh', 'x.n0g.xyz',
)
REDDIT_HOSTS = ('redlib.catsarch.com', 'redlib.nadeko.net', 'redlib.privadency.com',
                'safereddit.com', 'red.artemislena.eu', 'redlib.privacyredirect.com')
HOSTS = NITTER_HOSTS + REDDIT_HOSTS
ROUTES = ('rss', 'root', 'pristine')


def endpoints_for(host, route):
    if host not in HOSTS or host in EXCLUDED:
        raise ValueError('host outside the reviewed public fleet')
    if route not in ROUTES or (host in NITTER_HOSTS and route != 'rss'):
        raise ValueError('route not applicable to this host')
    if host in NITTER_HOSTS:
        return {account: (f'https://{host}/{account}/rss', 'twitter_feed', False)
                for account in ACCOUNTS}
    suffix, kind, pristine = {
        'rss': ('/new/.rss', 'reddit_feed', False),
        'root': ('', 'listing', False),
        'pristine': ('/new?limit=100', 'listing', True),
    }[route]
    return {game: (f'https://{host}/r/{sub}{suffix}', kind, pristine)
            for game, sub in base.SUBREDDITS.items()}


def probe_bounded(host, route, endpoint):
    command = [sys.executable, str(Path(__file__).resolve()), '--host', host,
               '--route', route, '--endpoint', endpoint]
    try:
        run = subprocess.run(command, capture_output=True, text=True,
                             timeout=base.ENDPOINT_DEADLINE, check=False)
    except subprocess.TimeoutExpired:
        return {'endpoint': endpoint, 'body_class': 'total_deadline_exceeded', 'candidate_response': False}
    if run.returncode:
        return {'endpoint': endpoint, 'body_class': 'probe_worker_failed', 'candidate_response': False}
    try:
        result = json.loads(run.stdout)
    except json.JSONDecodeError:
        return {'endpoint': endpoint, 'body_class': 'invalid_worker_output', 'candidate_response': False}
    return result


def collect(host, route, cooldown_file):
    endpoints = endpoints_for(host, route)
    # A job has one host; nevertheless validate the file's host before applying it.
    stopped = False
    if cooldown_file and cooldown_file.exists():
        stopped = json.loads(cooldown_file.read_text()).get('host') == host
    results = []
    for i, (name, (url, kind, pristine)) in enumerate(endpoints.items()):
        if stopped:
            row = {'endpoint': name, 'requested_url': url,
                   'body_class': 'not_requested_after_429', 'candidate_response': False,
                   'request_attempted': False}
        else:
            if i or route != 'rss':
                time.sleep(PAUSE_SECONDS)
            row = probe_bounded(host, route, name)
            row['request_attempted'] = True
            row.setdefault('requested_url', url)
            row.setdefault('kind', kind)
            row.setdefault('pristine_request', pristine)
            if row.get('http_status') == 429:
                stopped = True
                if cooldown_file:
                    cooldown_file.write_text(json.dumps({'host': host, 'stopped_utc': base.utc_now(),
                                                        'reason': 'HTTP 429; no further requests this job'}))
        row.update({'host': host, 'route': route})
        results.append(row)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=HOSTS, required=True)
    parser.add_argument('--route', choices=ROUTES, default='rss')
    parser.add_argument('--endpoint', help=argparse.SUPPRESS)
    parser.add_argument('--cooldown-file', type=Path)
    parser.add_argument('--output', type=Path, required=False)
    parser.add_argument('--annotations', action='store_true')
    args = parser.parse_args()
    endpoints = endpoints_for(args.host, args.route)
    # Replace, not extend: the first two audits' excluded URLs are inaccessible.
    base.ENDPOINTS = endpoints
    if args.endpoint:
        if args.endpoint not in endpoints:
            parser.error('endpoint outside selected host/route')
        print(json.dumps(base.fetch_endpoint(args.endpoint), ensure_ascii=True))
        return
    if args.output is None:
        parser.error('--output is required for a full route probe')
    report = {'host': args.host, 'route': args.route, 'generated_utc': base.utc_now(),
              'github_actions': os.getenv('GITHUB_ACTIONS') == 'true',
              'runner_os': os.getenv('RUNNER_OS', 'unknown'),
              'runner_arch': os.getenv('RUNNER_ARCH', 'unknown'),
              'runner_environment': os.getenv('RUNNER_ENVIRONMENT', 'unknown'),
              'run_id': os.getenv('GITHUB_RUN_ID', ''),
              'note': 'No excluded hosts or tokens; 429 skips are not observed failures. Cloud/region not inferred.',
              'results': collect(args.host, args.route, args.cooldown_file)}
    data = json.dumps(report, indent=2, ensure_ascii=True) + '\n'
    args.output.write_text(data)
    print(data, end='')
    if args.annotations:
        for command in base.annotation_commands(report):
            print(command)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
            stream.write(f'\n### {args.host} — {args.route}\n')
            stream.write(base.summary(report))


if __name__ == '__main__':
    main()
