#!/usr/bin/env python3
"""Read-only source/baseline audit. Never invokes monitors, PRs, merges or pushes.

Reads every tracked file, parses every Python/JSON file, inventories environment
references and local Markdown links, runs existing offline CI commands, and
reproduces selected current maintenance/reporting gaps with synthetic fixtures.
Findings are not silently treated as repaired merely because baseline tests pass.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.parse import unquote


def command(root, argv, timeout=240):
    start = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=root, text=True, capture_output=True, timeout=timeout, check=False)
        lines = (p.stdout + '\n' + p.stderr).splitlines()
        # Only known test summaries, not arbitrary log lines/config values.
        summary = [line for line in lines if 'ALL PASS' in line or re.match(r'^(OK|Ran \d+ tests|\d+ passed)', line)]
        return {'command': argv, 'exit_code': p.returncode,
                'elapsed_seconds': round(time.monotonic() - start, 3), 'summary': summary[-8:]}
    except subprocess.TimeoutExpired:
        return {'command': argv, 'exit_code': None, 'timed_out': True,
                'elapsed_seconds': round(time.monotonic() - start, 3)}


def tracked_files(root):
    p = subprocess.run(['git', 'ls-files', '-z'], cwd=root, capture_output=True, check=True)
    return [Path(os.fsdecode(name)) for name in p.stdout.split(b'\0') if name]


def scan(root):
    inventory, errors, env_refs, md_links, examples = [], [], [], [], []
    texts = {}
    for relative in tracked_files(root):
        path = root / relative
        if path.is_symlink():
            errors.append({'file': str(relative), 'error': 'symlink not followed'})
            continue
        data = path.read_bytes()  # Entire file, no byte/line truncation.
        item = {'path': str(relative), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            item['kind'] = 'binary'; inventory.append(item); continue
        item.update(kind='text', lines=len(text.splitlines()))
        inventory.append(item); texts[str(relative)] = text
        if relative.suffix == '.py':
            try:
                tree = ast.parse(text, filename=str(relative))
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call): continue
                    fn = ast.unparse(node.func)
                    pos = 1 if fn == '_env' else 0
                    if fn not in ('os.getenv', 'os.environ.get', 'os.environ.setdefault', '_env'):
                        continue
                    if len(node.args) > pos and isinstance(node.args[pos], ast.Constant) and isinstance(node.args[pos].value, str):
                        env_refs.append({'file': str(relative), 'line': node.lineno, 'name': node.args[pos].value, 'reader': fn})
                    else:
                        env_refs.append({'file': str(relative), 'line': node.lineno, 'name': '<dynamic>', 'reader': fn})
            except (SyntaxError, ValueError) as exc:
                errors.append({'file': str(relative), 'error': type(exc).__name__})
        if relative.suffix == '.json':
            try: json.loads(text)
            except (json.JSONDecodeError, ValueError): errors.append({'file': str(relative), 'error': 'invalid JSON'})
        if relative.suffix == '.md':
            for match in re.finditer(r'\]\(([^\s)]+)\)', text):
                link = match.group(1)
                if link.startswith(('#', 'http:', 'https:', 'mailto:', '/')) or '${' in link: continue
                target = unquote(link.split('#', 1)[0])
                if target and not (path.parent / target).exists():
                    md_links.append({'file': str(relative), 'target': link, 'status': 'candidate_missing_link_manual_review'})
        if relative.name == '.env.example':
            examples += [{'file': str(relative), 'line': n, 'name': m.group(1)}
                         for n, line in enumerate(text.splitlines(), 1)
                         if (m := re.match(r'^\s*#?\s*([A-Z][A-Z0-9_]+)\s*=', line))]
    return {'inventory': inventory, 'parse_errors': errors, 'environment_references': env_refs,
            'env_example_keys': examples, 'markdown_link_candidates': md_links}, texts


def news_findings(root, texts):
    findings = []
    workflow = texts['.github/workflows/twitter_monitor.yml']
    engine = texts['testing area/twitter_v3.py']
    timestamped = '2026-10-15 10:00:00,000 [INFO] [TYPEII_EN] feed OK via https://nitter.cf — 17 entries.\n'
    # Execute the exact account-counter awk expression extracted from the workflow.
    match = re.search(r"accounts_checked=\$\(awk '([^']+)'", workflow)
    if match:
        p = subprocess.run(['awk', match.group(1)], input=timestamped, text=True, capture_output=True, check=True)
        findings.append({'id': 'twitter-summary-prefix', 'fixture_feed_lines': 1,
                         'reported_account_matches': len(p.stdout.splitlines()),
                         'timestamp_format_present': '%(asctime)s [%(levelname)s]' in engine,
                         'status': 'reproduced' if not p.stdout.strip() else 'not_reproduced'})
    else:
        findings.append({'id': 'twitter-summary-prefix', 'status': 'pattern_changed_review_needed'})
    required = ['README.md', 'docs/PYTHON_RUNTIME.md', 'docs/CI_SMOKE.md', 'docs/DEPENDABOT.md']
    bump = texts['.github/workflows/python_version_bump.yml']
    missing = [p for p in required if p in bump and not (root / p).exists()]
    findings.append({'id': 'runtime-bump-docless-profile', 'missing_required_rewrite_files': missing,
                     'status': 'reproduced' if missing else 'development_docs_present'})
    merge = texts['.github/workflows/dependabot_auto_merge.yml']
    allowed = re.search(r'const allowedConclusions = .*?;', merge)
    classifier = re.search(r'const classifyChecks = checks => \{.*?\n            \};', merge, re.S)
    if allowed and classifier:
        # Only the pure classifier is executed; no GitHub client or merge function.
        js = allowed.group(0) + '\n' + classifier.group(0) + '''
const fixtures = {
 unrelated_success: [{name:'unrelated',status:'completed',conclusion:'success'}],
 skipped_required: [{name:'smoke',status:'completed',conclusion:'skipped'}],
 neutral_required: [{name:'smoke',status:'completed',conclusion:'neutral'}],
 failed_required: [{name:'smoke',status:'completed',conclusion:'failure'}]
};
console.log(JSON.stringify(Object.fromEntries(Object.entries(fixtures).map(([k,v])=>[k,classifyChecks(v)]))));
'''
        p = subprocess.run(['node', '-e', js], text=True, capture_output=True, check=True, timeout=15)
        findings.append({'id': 'current-check-classifier', 'fixture_outcomes': json.loads(p.stdout),
                         'status': 'current_behavior_not_repaired'})
    findings.append({'id': 'floating-package-resolution', 'status': 'present',
                     'note': 'requirements ranges are installed directly; no frozen runtime package graph'})
    return findings


def game_findings(root, texts):
    path = root / '.github/scripts/python_version_bump.py'
    spec = importlib.util.spec_from_file_location('reviewed_python_bump', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    data = [{'version': v, 'stable': True, 'files': [{'platform': 'linux', 'arch': 'x64'}]}
            for v in ('3.15.9', '3.15.10')]
    selected = module.highest_stable_minor(data)
    arm = module.highest_stable_minor([{'version': '3.15.0', 'stable': True,
                                        'files': [{'platform': 'linux', 'arch': 'arm64'}]}])
    return [
        {'id': 'numeric-version-selection', 'fixture_versions': ['3.15.9', '3.15.10'],
         'selected': selected, 'status': 'reproduced' if selected[1] == '3.15.9' else 'not_reproduced'},
        {'id': 'runner-architecture-selection', 'arm64_only_selected': arm is not None,
         'status': 'reproduced' if arm else 'not_reproduced'},
        {'id': 'floating-runtime-and-packages', 'status': 'present',
         'note': 'series pin plus direct requirements-range installation; no frozen runtime graph'},
        {'id': 'summary-before-git-push', 'status': 'present',
         'note': 'runner.write_summary precedes the separate monitor.yml state-push step'},
    ]


def emit(record):
    value = json.dumps(record, ensure_ascii=True, separators=(',', ':'))
    value = value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    print('::notice title=Maintenance baseline audit::' + value)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--family', choices=('news', 'game'), required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args(); root = args.root.resolve()
    source_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    audit, texts = scan(root)
    findings = news_findings(root, texts) if args.family == 'news' else game_findings(root, texts)
    if args.family == 'news':
        commands = [[sys.executable, '-m', 'compileall', '-q', 'testing area', 'tests'],
                    *[[sys.executable, f'tests/{name}.py'] for name in
                      ('test_smoke', 'test_reddit_signals', 'test_twitter_media')]]
    else:
        commands = [[sys.executable, '-m', 'compileall', '-q', 'gamexpress', 'tests', '.github/scripts'],
                    [sys.executable, '-m', 'gamexpress', 'validate'],
                    *[[sys.executable, f'tests/{name}.py'] for name in
                      ('test_smoke', 'test_schedule_epithet_and_settled', 'test_gachawiki_placeholder')],
                    [sys.executable, '-m', 'gamexpress', 'preview', '--out',
                     str(Path(tempfile.gettempdir()) / 'maintenance-audit-previews')]]
    results = [command(root, argv) for argv in commands]
    inventory_json = json.dumps(audit['inventory'], sort_keys=True).encode()
    context = {'family': args.family, 'repository': os.getenv('AUDITED_REPOSITORY', ''),
               'source_sha': source_sha, 'run_id': os.getenv('GITHUB_RUN_ID', ''),
               'python': sys.version.split()[0], 'runner_environment': os.getenv('RUNNER_ENVIRONMENT', ''),
               'runner_image': os.getenv('ImageOS', ''), 'runner_image_version': os.getenv('ImageVersion', ''),
               'files_fully_read': len(audit['inventory']),
               'bytes_read': sum(f['bytes'] for f in audit['inventory']),
               'inventory_sha256': hashlib.sha256(inventory_json).hexdigest(),
               'parse_errors': audit['parse_errors'],
               'baseline_passed': all(r['exit_code'] == 0 for r in results),
               'interpretation': 'Current baseline tested; findings remain. Proposed restructuring not implemented or certified.',
               'packages': {p: importlib.metadata.version(p) for p in ('aiohttp', 'feedparser', 'python-dotenv', 'PyYAML')}}
    report = {'context': context, 'commands': results, 'findings': findings, 'scan': audit}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    emit({'record': 'context', **context})
    emit({'record': 'baseline_commands', 'commands': results})
    emit({'record': 'findings', 'findings': findings})
    emit({'record': 'scan_summary', 'env_read_sites': len(audit['environment_references']),
          'env_example_keys': len(audit['env_example_keys']),
          'markdown_link_candidates': audit['markdown_link_candidates']})
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write(f"## Maintenance baseline audit — {context['repository']}\n\n")
            f.write(f"Source `{source_sha}`; {context['files_fully_read']} tracked files fully read.\n\n")
            f.write(f"Baseline checks: {'PASS' if context['baseline_passed'] else 'FAIL'}.\n\n")
            f.write('**This is not a clean-audit certificate or proof of future changes.** Known findings remain:\n\n')
            for finding in findings: f.write(f"- `{finding['id']}`: {finding['status']}\n")
    if not context['baseline_passed'] or audit['parse_errors']: raise SystemExit(1)


if __name__ == '__main__':
    main()
