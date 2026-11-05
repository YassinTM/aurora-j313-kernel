#!/usr/bin/env python3
"""Follow Aurora's Fedora kernel package (aurora-silicon/fedora-aurora).

Pins the kernel commit and release that package builds and copies its
config files into aurora/. Only rewrites anything when the kernel package
itself changed. Outputs (GITHUB_OUTPUT): changed, packaging_changed.
Writes $RUNNER_TEMP/{track.md,commit-msg.txt,packaging.diff}.
"""
import difflib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO = 'aurora-silicon/fedora-aurora'
PKG = 'packages/kernel-aurora/'
FILES = ['kernel-aurora.spec', 'config', 'fedora.config', 'validate-config.py']
ROOT = Path(__file__).resolve().parent.parent
TMP = Path(os.environ.get('RUNNER_TEMP', '/tmp'))


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'aurora-j313-kernel'})
    token = os.environ.get('GITHUB_TOKEN')
    if token and url.startswith('https://api.github.com/'):
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def output(**kw):
    lines = ''.join(f'{k}={v}\n' for k, v in kw.items())
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(lines)
    print(lines, end='')


def packaging(spec):
    """The spec without what changes on every release: pin, release, changelog."""
    spec = spec.split('\n%changelog', 1)[0]
    spec = re.sub(r'^%global commit .*$', '%global commit <pin>', spec, flags=re.M)
    return re.sub(r'^Release: .*$', 'Release: <release>', spec, flags=re.M)


def changelog(spec):
    return spec.split('\n%changelog\n', 1)[1] if '\n%changelog\n' in spec else ''


def main():
    head = json.loads(get(f'https://api.github.com/repos/{REPO}/commits/main'))['sha']
    raw = f'https://raw.githubusercontent.com/{REPO}/{head}/'
    new = {name: get(raw + PKG + name).decode() for name in FILES}
    source = json.loads(get(raw + 'sources.json'))['kernel-aurora']
    spec = new['kernel-aurora.spec']
    commit = re.search(r'^%global commit (\S+)', spec, re.M).group(1)
    version = re.search(r'^Version:\s*(\S+)', spec, re.M).group(1)
    release = re.search(r'^Release:\s*(\d+)', spec, re.M).group(1)
    if source['commit'] != commit or source['version'] != version:
        # Caught between two commits of an update; the next run sees both.
        sys.exit(f'sources.json ({source["commit"]}) and the spec ({commit}) disagree; not tracking this run')

    pin_file = ROOT / 'upstream.json'
    old_pin = json.loads(pin_file.read_text()) if pin_file.exists() else {}
    old = {name: (ROOT / 'aurora' / name).read_text() if (ROOT / 'aurora' / name).exists() else ''
           for name in FILES}
    pin = {'version': version, 'aurora_release': release, 'kernel_commit': commit,
           'kernel_sha256': source['sha256'], 'fedora_aurora_commit': head}
    same_pin = all(old_pin.get(k) == pin[k] for k in pin if k != 'fedora_aurora_commit')
    if same_pin and old == new:
        output(changed='false', packaging_changed='false')
        return

    for name, text in new.items():
        (ROOT / 'aurora' / name).write_text(text)
    pin_file.write_text(json.dumps(pin, indent=2) + '\n')

    old_ver = f"{old_pin.get('version', '?')}-{old_pin.get('aurora_release', '?')}"
    title = f'Track kernel-aurora {version}-{release} ({commit[:12]})'
    added = changelog(spec)
    if old['kernel-aurora.spec'] and changelog(old['kernel-aurora.spec']) in added:
        added = added[:added.index(changelog(old['kernel-aurora.spec']))]
    notes = (f'kernel-aurora {old_ver} -> {version}-{release}\n'
             f'aurora-silicon/linux {old_pin.get("kernel_commit", "?")[:12]} -> {commit[:12]}\n'
             f'fedora-aurora {head[:12]}\n\n{added.strip()}\n')
    (TMP / 'track.md').write_text(f'### {title}\n\n```\n{notes}```\n')
    (TMP / 'commit-msg.txt').write_text(f'{title}\n\n{notes}')

    diff = []
    for name in FILES:
        a, b = old[name], new[name]
        if name == 'kernel-aurora.spec':
            a, b = packaging(a), packaging(b)
        if name == 'config':
            continue  # Kconfig churn; the build validates the fragments instead.
        diff += difflib.unified_diff(a.splitlines(True), b.splitlines(True),
                                     f'a/aurora/{name}', f'b/aurora/{name}')
    (TMP / 'packaging.diff').write_text(''.join(diff))
    output(changed='true', packaging_changed='true' if diff and old_pin else 'false')


if __name__ == '__main__':
    main()
