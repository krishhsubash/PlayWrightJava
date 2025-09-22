import json, os, sys, urllib.request

HISTORY_PATH = 'combined/flaky-history.json'
WEBHOOK = os.environ.get('SLACK_WEBHOOK_URL')

def main():
    if not WEBHOOK:
        print('No SLACK_WEBHOOK_URL provided; skipping.')
        return 0
    if not os.path.isfile(HISTORY_PATH):
        print(f'Missing {HISTORY_PATH}; skipping.')
        return 0
    try:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print('Failed to read history file:', e)
        return 0
    if not isinstance(data, list) or len(data) < 2:
        print('Not enough history entries to compare; skipping.')
        return 0
    prev, curr = data[-2], data[-1]
    prev_flaky = len(prev.get('flaky_candidates', []))
    curr_flaky = len(curr.get('flaky_candidates', []))
    if curr_flaky > prev_flaky:
        msg = f"Flaky tests increased: {prev_flaky} -> {curr_flaky}"
        payload = json.dumps({'text': msg}).encode()
        try:
            req = urllib.request.Request(WEBHOOK, data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as resp:  # noqa: S310 (controlled URL)
                print('Slack notification sent, status:', resp.status)
        except Exception as e:  # noqa: BLE001
            print('Slack notification failed:', e)
    else:
        print(f'No increase in flaky tests (prev={prev_flaky}, curr={curr_flaky}).')
    return 0

if __name__ == '__main__':
    sys.exit(main())
