#!/usr/bin/env python3
"""Watch the upstream pull requests our patches come from (patches/upstream-prs.json).

Opens an issue when one is merged, closed, or gets new commits, and records
what it saw in the JSON (the workflow commits that). Needs GH_TOKEN for gh.
"""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = Path(os.environ.get('RUNNER_TEMP', '/tmp'))
WATCH = ROOT / 'patches' / 'upstream-prs.json'


def gh(*args):
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True).stdout


def main():
    watched = json.loads(WATCH.read_text())
    for entry in watched:
        repo, number = entry['repo'], entry['number']
        pr = json.loads(gh('api', f'repos/{repo}/pulls/{number}'))
        state = 'merged' if pr['merged_at'] else pr['state']
        head = pr['head']['sha']
        if state == entry['seen_state'] and head == entry['seen_head']:
            continue
        url = pr['html_url']
        if state == 'merged':
            title = f'{repo}#{number} merged: {entry["patch"]} can probably go'
            text = (f'[{pr["title"]}]({url}) was merged into `{pr["base"]["ref"]}`.\n\n'
                    f'Once Aurora\'s Fedora kernel package tracks a commit containing it, the daily check '
                    f'will report `{entry["patch"]}` as already upstream and build without it.\n\n'
                    f'Why we carry it: {entry["why"]}')
        elif state == 'closed':
            title = f'{repo}#{number} closed without merging'
            text = (f'[{pr["title"]}]({url}) was closed unmerged. We keep carrying `{entry["patch"]}`; '
                    f'check the PR discussion for why, in case the fix went in another way.')
        else:
            title = f'{repo}#{number} changed'
            diff = gh('api', f'repos/{repo}/pulls/{number}', '-H', 'Accept: application/vnd.github.diff')
            text = (f'[{pr["title"]}]({url}) has new commits (`{entry["seen_head"][:12]}` -> `{head[:12]}`). '
                    f'Compare it with `patches/{entry["patch"]}`; if the fix itself changed, refresh our copy.\n\n'
                    f'<details><summary>Current PR diff</summary>\n\n```diff\n{diff[:60000]}\n```\n</details>')
        body = TMP / f'pr-{number}.md'
        body.write_text(text + '\n')
        key = TMP / f'pr-{number}.key'
        key.write_text(f'{state} {head}\n')
        subprocess.run(['bash', str(ROOT / 'scripts' / 'issue.sh'), title, str(body), str(key)], check=True)
        entry['seen_state'], entry['seen_head'] = state, head
    WATCH.write_text(json.dumps(watched, indent=2) + '\n')


if __name__ == '__main__':
    main()
