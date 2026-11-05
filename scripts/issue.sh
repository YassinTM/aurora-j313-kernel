#!/usr/bin/env bash
# issue.sh TITLE BODY_FILE [KEY_FILE]: open an issue, or comment on the open
# issue with the same title. KEY_FILE (default BODY_FILE) is what identifies
# the finding; pass the deterministic part, not the AI text. If that finding
# was already posted, nothing is posted, so a daily run stays quiet.
set -euo pipefail
title=$1 body=$2 key=${3:-$2}
mark="<!-- finding:$(sha256sum <"$key" | cut -c1-16) -->"
printf '\n%s\n' "$mark" >>"$body"
number=$(gh issue list --state open --limit 100 --json number,title |
	python3 -I -c 'import json,sys; t=sys.argv[1]; print(next((i["number"] for i in json.load(sys.stdin) if i["title"] == t), ""))' "$title")
if [[ -z $number ]]; then
	gh issue create --title "$title" --body-file "$body"
elif gh issue view "$number" --json body,comments --jq '.body, .comments[].body' | grep -qF "$mark"; then
	echo "Issue #$number already says this"
else
	gh issue comment "$number" --body-file "$body"
fi
