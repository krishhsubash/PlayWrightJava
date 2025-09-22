#!/usr/bin/env python3
import json, sys
from pathlib import Path

history_file = Path('target/flaky-history.json')
if not history_file.exists():
    print('No history file found, skipping trends.')
    sys.exit(0)

data = json.loads(history_file.read_text())
# Build arrays for chart
points = list(range(1, len(data)+1))
failed = [run['summary']['failed'] for run in data]
totals = [max(1, run['summary'].get('total', 0)) for run in data]
failure_rates = [round((f/t)*100, 2) for f, t in zip(failed, totals)]
flaky_counts = [len(run.get('flaky_candidates', [])) for run in data]

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'/>
<title>Test Trend</title>
<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
<style>body{{font-family:Arial, sans-serif; margin:20px}} canvas{{max-width:900px;}}</style>
</head>
<body>
<h1>Test Execution Trends</h1>
<canvas id='failChart'></canvas>
<canvas id='failureRateChart' style='margin-top:40px;'></canvas>
<canvas id='flakyChart' style='margin-top:40px;'></canvas>
<script>
const labels = {points};
const failedData = {failed};
const flakyData = {flaky_counts};
const failureRateData = {failure_rates};
new Chart(document.getElementById('failChart').getContext('2d'), {{
  type:'line',
  data: {{ labels: labels, datasets:[{{label:'Failed Tests', data: failedData, borderColor:'#d33', fill:false}}] }},
  options: {{ responsive:true, plugins: {{ legend: {{ position:'top'}} }}, scales: {{ y: {{ beginAtZero:true }} }} }}
}});
new Chart(document.getElementById('failureRateChart').getContext('2d'), {{
  type:'line',
  data: {{ labels: labels, datasets:[{{label:'Failure Rate (%)', data: failureRateData, borderColor:'#36c', fill:false}}] }},
  options: {{ responsive:true, plugins: {{ legend: {{ position:'top'}} }}, scales: {{ y: {{ beginAtZero:true, title: {{ display:true, text:'% Failed'}} }} }} }}
}});
new Chart(document.getElementById('flakyChart').getContext('2d'), {{
  type:'line',
  data: {{ labels: labels, datasets:[{{label:'Flaky Candidates', data: flakyData, borderColor:'#f90', fill:false}}] }},
  options: {{ responsive:true, plugins: {{ legend: {{ position:'top'}} }}, scales: {{ y: {{ beginAtZero:true }} }} }}
}});
</script>
</body>
</html>
"""

out = Path('target/trends.html')
out.write_text(html)
print('Wrote', out)
