#!/usr/bin/env bash
# Decide whether to build: hash every build input and look for a release that
# already carries that hash. Outputs (GITHUB_OUTPUT): build, key, tag,
# j313_release. FORCE=true builds anyway. SKIP_PATCHES lists patches left out.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

inputs=(upstream.json aurora/config aurora/fedora.config aurora/validate-config.py
	config/j313.config kernel-aurora-j313.spec.in scripts/build-rpm.sh)
for p in patches/*.patch; do
	[[ " ${SKIP_PATCHES:-} " == *" $(basename "$p") "* ]] || inputs+=("$p")
done
key=$(python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); d.pop("fedora_aurora_commit"); print(json.dumps(d, sort_keys=True))' upstream.json |
	cat - "${inputs[@]:1}" | sha256sum | cut -c1-24)
base=$(python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["version"] + "-" + d["aurora_release"])' upstream.json)

releases=$(gh api --paginate "repos/$GITHUB_REPOSITORY/releases?per_page=100" --jq '.[] | [.tag_name, .body] | @json')
build=true
if grep -qF "build-key: $key" <<<"$releases" && [[ ${FORCE:-false} != true ]]; then
	build=false
fi
last=$(python3 -I -c '
import json, re, sys
base = sys.argv[1]
nums = [int(m.group(1)) for line in sys.stdin if line.strip()
        for m in [re.fullmatch(re.escape(base) + r"\.(\d+)", json.loads(line)[0])] if m]
print(max(nums, default=0))' "$base" <<<"$releases")
n=$((last + 1))

echo "build=$build key=$key tag=$base.$n"
{
	echo "build=$build"
	echo "key=$key"
	echo "tag=$base.$n"
	echo "j313_release=$n"
} >>"${GITHUB_OUTPUT:-/dev/null}"
