#!/usr/bin/env python3
import json, sys, pathlib, os
base = pathlib.Path('combined/history')
merged = []
max_history = int(os.environ.get('FLAKY_HISTORY_MAX', '200'))
if base.exists():
    for f in sorted(base.glob('flaky-history.json')):
        try:
            data = json.loads(f.read_text())
            if isinstance(data, list):
                merged.extend(data)
            else:
                merged.append(data)
        except Exception:
            pass
out = pathlib.Path('combined/flaky-history.json')
out.parent.mkdir(parents=True, exist_ok=True)
if len(merged) > max_history:
    merged = merged[-max_history:]
out.write_text(json.dumps(merged, indent=2))
print('Merged entries (post-prune):', len(merged))
