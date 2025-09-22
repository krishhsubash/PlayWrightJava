#!/usr/bin/env python3
import json, os, re, subprocess, datetime
from pathlib import Path

HISTORY = Path('combined/flaky-history.json')
BADGES_DIR = Path('site/badges')
OUT = Path('site/index.html')

def read_badge(name):
    f = BADGES_DIR / name
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            return None
    return None

def main():
    BADGES_DIR.mkdir(parents=True, exist_ok=True)
    history = []
    if HISTORY.exists():
        try:
            history = json.loads(HISTORY.read_text())
        except Exception:
            history = []
    latest = history[-1] if history else {}
    summary = latest.get('summary', {})
    flaky = len(latest.get('flaky_candidates', []))
    fail_rate = 0.0
    if summary.get('total'):
        fail_rate = (summary.get('failed', 0) / summary.get('total', 1)) * 100
    stability = 100 - fail_rate
    retry_stats = latest.get('retry_stats', {})
    flaky_passes = latest.get('flaky_passes', [])

    flaky_badge = read_badge('flaky-badge.json')
    failure_badge = read_badge('failure-badge.json')
    stability_badge = read_badge('stability-badge.json')

    # Build history table (last N runs)
    last_n = history[-20:] if len(history) > 20 else history
    rows = []
    for idx, run in enumerate(last_n, start=len(history)-len(last_n)+1):
        summ = run.get('summary', {})
        fr = 0.0
        if summ.get('total'):
            fr = (summ.get('failed',0) / max(1, summ.get('total',1))) * 100
        rows.append((idx, run.get('timestamp',''), summ.get('total',0), summ.get('failed',0), len(run.get('flaky_candidates', [])), f"{fr:.1f}%"))

    import json as _json
    failure_series = [r[3] for r in rows]
    flaky_series = [r[4] for r in rows]
    fail_rate_series = [float(r[5].rstrip('%')) for r in rows]
    # Determine commit hash (short) if available
    commit = os.environ.get('GITHUB_SHA', '')[:7]
    allure_index = Path('site/allure/index.html')
    allure_ts = ''
    if allure_index.exists():
        try:
            mtime = datetime.datetime.utcfromtimestamp(allure_index.stat().st_mtime)
            allure_ts = mtime.strftime('%Y-%m-%d %H:%M:%S UTC')
        except Exception:
            allure_ts = ''
    html = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/><title>Test Quality Dashboard</title>
<link rel='preconnect' href='https://img.shields.io'>
<style>
 body {{font-family: system-ui, Arial, sans-serif; margin: 20px;}}
 header {{display:flex; gap:1rem; flex-wrap:wrap; align-items:center;}}
 nav.breadcrumb {{font-size:14px; margin-top:4px;}}
 nav.breadcrumb a {{text-decoration:none; color:#0366d6;}}
 nav.breadcrumb span.sep {{color:#555; margin:0 4px;}}
 section {{margin-top:40px;}}
 code {{background:#f5f5f5; padding:2px 4px; border-radius:3px;}}
 .grid {{display:grid; gap:16px; grid-template-columns: repeat(auto-fit, minmax(260px,1fr));}}
 .card {{border:1px solid #ddd; border-radius:8px; padding:16px; background:#fff; box-shadow:0 1px 2px rgba(0,0,0,0.06);}}
 h2 {{margin-top:0;}}
 a.badge-link img {{vertical-align:middle;}}
 .sparkline {{ width:120px; height:30px; }}
 #historyFilter {{ margin-bottom:8px; padding:4px; }}
</style></head>
<body>
<header>
    <div>
        <h1 style='margin:0;'>Test Quality Dashboard</h1>
        <nav class='breadcrumb'>
            <a href='./'>Dashboard</a><span class='sep'>/</span><a href='allure/'>Allure</a>
            {f"<span class='sep'>|</span><span>Commit: {commit}</span>" if commit else ''}
            {f"<span class='sep'>|</span><span>Allure: {allure_ts}</span>" if allure_ts else ''}
        </nav>
    </div>
  <a class='badge-link' href='extra/trends.html'><img src='badges/flaky-badge.json' alt='Flaky Count (JSON)' hidden></a>
  <img src='https://img.shields.io/endpoint?url={os.environ.get('SITE_BASE','') + 'badges/flaky-badge.json'}' alt='Flaky'>
  <img src='https://img.shields.io/endpoint?url={os.environ.get('SITE_BASE','') + 'badges/failure-badge.json'}' alt='Failure Rate'>
  <img src='https://img.shields.io/endpoint?url={os.environ.get('SITE_BASE','') + 'badges/stability-badge.json'}' alt='Stability'>
</header>
<p>Latest run summary: Total={summary.get('total',0)} Passed={summary.get('passed',0)} Failed={summary.get('failed',0)} Skipped={summary.get('skipped',0)} | Flaky={flaky} | Failure Rate={fail_rate:.1f}% | Stability={stability:.1f}</p>
<button id='toggleSparks' style='margin:4px 0;'>Hide Sparklines</button>
<div id='sparkContainer'>
    <canvas id='sparkFailures' class='sparkline'></canvas>
    <canvas id='sparkFlaky' class='sparkline'></canvas>
    <canvas id='sparkFailRate' class='sparkline'></canvas>
    <div style='font-size:12px;color:#555;margin-top:4px;'>Sparklines (left to right): failed tests, flaky candidates, failure rate %. Latest point is rightmost.</div>
</div>
<div class='grid'>
  <div class='card'>
    <h2>Trends</h2>
    <p>View historical charts for failures, failure rate, and flaky candidates.</p>
    <p><a href='extra/trends.html'>Open Trends &raquo;</a></p>
  </div>
    <div class='card'>
        <h2>Allure Report</h2>
        <p>Interactive test report (steps, attachments, traces, videos).</p>
        <p><a href='allure/'>Open Allure &raquo;</a></p>
    </div>
  <div class='card'>
    <h2>Artifacts</h2>
    <p>Per-matrix artifacts (traces, screenshots, videos) available in workflow run artifacts section.</p>
    <p><a href='test-summary.md'>Aggregated Test Summary</a></p>
  </div>
</div>
<section>
<h2>Reliability Formula</h2>
<p>Stability score = <code>100 - failure_rate_percent</code>, where <code>failure_rate_percent = failed / total * 100</code> from the most recent aggregated run.</p>
</section>
<section>
<h2>Flaky Candidates (Latest)</h2>
<ul>
"""
    for fc in latest.get('flaky_candidates', []):
        html += f"<li>{fc.get('class')}::{fc.get('name')}</li>"
    if not latest.get('flaky_candidates'):
        html += "<li>None</li>"
    html += """</ul>
</section>
<section>
<h2>Recovered (Flaky Pass) Tests</h2>
<ul>
"""
    for fp in flaky_passes:
        html += f"<li>{fp.get('class')}::{fp.get('name')} (attempts={fp.get('attempts')})</li>"
    if not flaky_passes:
        html += "<li>None</li>"
    html += """</ul>
</section>
<section>
<h2>Retry Statistics</h2>
<p>Retried tests: {retry_stats.get('retried_tests',0)} | Recovered: {retry_stats.get('recovered_tests',0)} | Recovery Rate: {retry_stats.get('recovery_rate',0)}%</p>
</section>
<section>
<h2>Recent Run History (Last {len(last_n)})</h2>
<input id='historyFilter' type='text' placeholder='Filter (substring)...'/>
<table id='historyTable' border='1' cellpadding='4' cellspacing='0'>
<thead><tr><th>#</th><th>Timestamp (UTC)</th><th>Total</th><th>Failed</th><th>Flaky</th><th>Fail %</th></tr></thead><tbody>
"""
    for r in rows:
        html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td></tr>"
    if not rows:
        html += "<tr><td colspan='6'>No history</td></tr>"
    html += """</tbody></table>
</section>
<section>
<h2>Failed Test Artifacts (Latest)</h2>
<ul>
"""
    # Attempt to map failed tests to trace artifacts heuristically (by index order)
    traces_dir = Path('combined/artifacts/traces')
    videos_dir = Path('combined/artifacts/videos')
    trace_files = {p.name: p for p in traces_dir.glob('*.zip')} if traces_dir.exists() else {}
    video_files = {p.name: p for p in videos_dir.glob('*.webm')} if videos_dir.exists() else {}
    failed_tests = latest.get('failed_tests', [])
    grouped = {}
    for ft in failed_tests:
        ap = ft.get('artifact_prefix', '')
        base = ap.split('-attempt')[0] if '-attempt' in ap else ap
        grouped.setdefault(base, []).append(ap)
    for base, attempts in grouped.items():
        html += f"<li>{base}"
        attempt_links = []
        for ap in sorted(attempts):
            t = next((n for n in trace_files.keys() if n.startswith(ap)), None)
            v = next((n for n in video_files.keys() if n.startswith(ap)), None)
            parts = []
            if t:
                parts.append(f"<a href='artifacts/traces/{t}'>trace</a>")
            if v:
                parts.append(f"<a href='artifacts/videos/{v}'>video</a>")
            label = ap.split('-attempt')[-1] if '-attempt' in ap else '1'
            attempt_links.append(f"attempt {label}: " + (', '.join(parts) if parts else 'no artifacts'))
        html += "<ul><li>" + "</li><li>".join(attempt_links) + "</li></ul></li>"
    if not grouped:
        html += "<li>None</li>"
    html += """</ul>
</section>
<footer style='margin-top:60px;font-size:12px;color:#666;'>Generated dashboard. History length = {len(history)}.</footer>
</body>
<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
<script>
const failureSeries = {_json.dumps(failure_series)};
const flakySeries = {_json.dumps(flaky_series)};
const failRateSeries = {_json.dumps(fail_rate_series)};
function spark(ctxId, data, color){
    new Chart(document.getElementById(ctxId).getContext('2d'), {type:'line', data:{labels:data.map((_,i)=>i+1), datasets:[{data, borderColor:color, tension:0.3, pointRadius:0}]}, options:{plugins:{legend:{display:false}}, scales:{x:{display:false},y:{display:false}}});}
spark('sparkFailures', failureSeries, '#d33');
spark('sparkFlaky', flakySeries, '#f90');
spark('sparkFailRate', failRateSeries, '#36c');
document.getElementById('toggleSparks').addEventListener('click', ()=>{
    const c = document.getElementById('sparkContainer');
    const btn = document.getElementById('toggleSparks');
    if (c.style.display === 'none') { c.style.display='block'; btn.textContent='Hide Sparklines'; }
    else { c.style.display='none'; btn.textContent='Show Sparklines'; }
});
document.getElementById('historyFilter').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#historyTable tbody tr');
    rows.forEach(r=>{ r.style.display = q && !r.innerText.toLowerCase().includes(q) ? 'none':'table-row'; });
});
</script>
</html>"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print('Dashboard written to', OUT)

if __name__ == '__main__':
    main()
