#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from pathlib import Path
import hashlib
import json
import os
from datetime import datetime

MAX_HISTORY = int(os.environ.get('FLAKY_HISTORY_MAX', '200'))

REPORT_DIR = Path('target/surefire-reports')

summary = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'suites': [],
    'flaky_candidates': []
}

if not REPORT_DIR.exists():
    print('No surefire reports found')
    exit(0)

def classify(case):
    if case.find('failure') is not None or case.find('error') is not None:
        return 'failed'
    if case.find('skipped') is not None:
        return 'skipped'
    return 'passed'

# Collect occurrences by (class,name) to detect instability across runs (hash of stacktrace)
occurrences = {}
failed_tests_current_run = []

for file in REPORT_DIR.glob('TEST-*.xml'):
    tree = ET.parse(file)
    root = tree.getroot()
    suite_name = root.attrib.get('name')
    suite_record = {'name': suite_name, 'tests': []}
    for case in root.findall('testcase'):
        name = case.attrib.get('name')
        classname = case.attrib.get('classname')
        status = classify(case)
        summary['total'] += 1
        summary[status] += 1
        failure_el = case.find('failure') or case.find('error')
        failure_hash = None
        if failure_el is not None:
            failure_hash = hashlib.sha256((failure_el.text or '').encode('utf-8')).hexdigest()[:10]
        key = (classname, name)
        if key not in occurrences:
            occurrences[key] = []
        occurrences[key].append({'status': status, 'failure_hash': failure_hash})
        if status == 'failed':
            attempt = os.environ.get('TEST_ATTEMPT') or os.environ.get('ATTEMPT') or os.getenv('ATTEMPT') or '1'
            try:
                attempt_int = int(attempt)
            except Exception:
                attempt_int = 1
            suffix = f"-attempt{attempt_int}" if attempt_int > 1 else ""
            failed_tests_current_run.append({'class': classname, 'name': name, 'artifact_prefix': f"{classname.split('.')[-1]}_{name}{suffix}"})
        suite_record['tests'].append({'name': name, 'class': classname, 'status': status, 'failure_hash': failure_hash})
    summary['suites'].append(suite_record)

# Detect flaky candidates: same test with both pass and fail states in its history (across parallel shards)
for key, runs in occurrences.items():
    statuses = {r['status'] for r in runs}
    if 'failed' in statuses and 'passed' in statuses:
        summary['flaky_candidates'].append({'test': key, 'runs': runs})

print(json.dumps(summary, indent=2))

# Flaky history merge
history_file = Path('target/flaky-history.json')
history = []
if history_file.exists():
    try:
        history = json.loads(history_file.read_text())
    except Exception:
        history = []

run_entry = {
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'summary': {
        'total': summary['total'],
        'passed': summary['passed'],
        'failed': summary['failed'],
        'skipped': summary['skipped']
    },
    'failed_tests': failed_tests_current_run,
    'flaky_candidates': [
        {'class': fc['test'][0], 'name': fc['test'][1], 'runs': fc['runs']}
        for fc in summary['flaky_candidates']
    ],
    'retry_stats': {},
    'flaky_passes': []
}

# Retry attempt analysis
retry_log = Path('target/retry-attempts.jsonl')
attempt_records = []
if retry_log.exists():
    for line in retry_log.read_text().splitlines():
        try:
            attempt_records.append(json.loads(line))
        except Exception:
            pass
if attempt_records:
    from collections import defaultdict
    grouped = defaultdict(list)
    for rec in attempt_records:
        key = (rec.get('class'), rec.get('method'))
        grouped[key].append(rec)
    totalRetried = 0
    recovered = 0
    for key, recs in grouped.items():
        attempts_sorted = sorted(recs, key=lambda r: r.get('attempt', 0))
        success_final = attempts_sorted[-1].get('success') if attempts_sorted else False
        had_failure = any(not r.get('success') for r in attempts_sorted[:-1])
        if len(attempts_sorted) > 1 and had_failure:
            totalRetried += 1
            if success_final:
                recovered += 1
                run_entry['flaky_passes'].append({'class': key[0], 'name': key[1], 'attempts': len(attempts_sorted)})
    if totalRetried:
        run_entry['retry_stats'] = {
            'retried_tests': totalRetried,
            'recovered_tests': recovered,
            'recovery_rate': round((recovered / totalRetried) * 100, 2)
        }

history.append(run_entry)
# Prune history if exceeding MAX_HISTORY (keep newest MAX_HISTORY)
if len(history) > MAX_HISTORY:
    history = history[-MAX_HISTORY:]
history_file.write_text(json.dumps(history, indent=2))
print('Updated', history_file)

# Generate markdown table
md_lines = []
md_lines.append('# Test Summary')
md_lines.append('')
md_lines.append(f"Total: {summary['total']}  Passed: {summary['passed']}  Failed: {summary['failed']}  Skipped: {summary['skipped']}")
md_lines.append('')
if summary['flaky_candidates']:
    md_lines.append('## Flaky Candidates')
    for fc in summary['flaky_candidates']:
        (cls, name) = fc['test']
        md_lines.append(f"- {cls}::{name} (runs: {len(fc['runs'])})")
else:
    md_lines.append('No flaky candidates detected.')

Path('target').mkdir(exist_ok=True)
md_lines.append('\n## Flaky History Size')
md_lines.append(str(len(history)))

Path('target/test-summary.md').write_text('\n'.join(md_lines))
print('Wrote target/test-summary.md')
