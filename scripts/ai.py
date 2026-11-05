#!/usr/bin/env python3
"""Ask Gemini to read some files: ai.py PROMPT_FILE INPUT_FILE...

Prints markdown. Never fails the job: without GEMINI_API_KEY, or on any
API error, it prints a short note instead. The output is advice only;
nothing in this repository applies it automatically.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

LIMIT = 400_000  # characters of input; the free tier allows 250k tokens a minute


def main():
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        print('_No AI read: add a `GEMINI_API_KEY` repository secret to get one._')
        return
    model = os.environ.get('GEMINI_MODEL') or 'gemini-3.8-flash'
    system = Path(sys.argv[1]).read_text()
    text = ''
    for name in sys.argv[2:]:
        text += f'===== FILE {name}\n{Path(name).read_text(errors="replace")}\n'
    body = {
        'system_instruction': {'parts': [{'text': system}]},
        'contents': [{'role': 'user', 'parts': [{'text': text[:LIMIT]}]}],
    }
    req = urllib.request.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': key})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            reply = json.load(r)
        parts = reply['candidates'][0]['content']['parts']
        answer = ''.join(p.get('text', '') for p in parts if not p.get('thought')).strip()
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError) as error:
        detail = error.read().decode(errors='replace')[:300] if isinstance(error, urllib.error.HTTPError) else ''
        print(f'_No AI read: {model} failed ({error}) {detail}_')
        return
    print(f'_{model}, advisory only. Check it before acting on it._\n\n{answer}')


if __name__ == '__main__':
    main()
