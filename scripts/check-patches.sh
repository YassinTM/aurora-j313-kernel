#!/usr/bin/env bash
# Check every patches/*.patch against the pinned kernel commit, in order:
#   applies   - carried as usual
#   upstream  - the reverse applies, so the kernel already has it; skipped
#   conflict  - neither; nothing gets built
# Fetches only the files the patches touch (blobless, sparse).
# Outputs (GITHUB_OUTPUT): status=ok|upstream|conflict, skip=<names>.
# Writes $RUNNER_TEMP/patch-report.md and, for conflicts, patch-context.txt
# (the patch, the current upstream files and what changed since the last
# release) for the AI step.
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
tmp=${RUNNER_TEMP:-/tmp}
commit=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["kernel_commit"])' "$root/upstream.json")
previous=${PREVIOUS_KERNEL_COMMIT:-}
patches=("$root"/patches/*.patch)
mapfile -t files < <(grep -h '^+++ b/' "${patches[@]}" | sed 's@^+++ b/@@' | sort -u)

src=$(mktemp -d)
git -C "$src" init -q
git -C "$src" remote add origin https://github.com/aurora-silicon/linux.git
git -C "$src" fetch -q --depth=1 --filter=blob:none origin "$commit"
git -C "$src" sparse-checkout set --no-cone "${files[@]}"
git -C "$src" checkout -q --detach FETCH_HEAD

status=ok skip=()
report=$tmp/patch-report.md context=$tmp/patch-context.txt
: >"$context"
{
	echo "### Patches against aurora-silicon/linux \`${commit:0:12}\`"
	echo
	echo '| Patch | Result |'
	echo '| --- | --- |'
} >"$report"
for p in "${patches[@]}"; do
	name=$(basename "$p")
	if git -C "$src" apply --check "$p" 2>/dev/null; then
		git -C "$src" apply "$p"
		echo "| \`$name\` | applies |" >>"$report"
	elif git -C "$src" apply --check -R "$p" 2>/dev/null; then
		skip+=("$name")
		[[ $status == conflict ]] || status=upstream
		echo "| \`$name\` | **already upstream**, left out of the build |" >>"$report"
	else
		status=conflict
		echo "| \`$name\` | **does not apply** |" >>"$report"
		{
			echo "===== PATCH $name"
			cat "$p"
			echo "===== git apply -v output"
			git -C "$src" apply --check -v "$p" 2>&1 || :
		} >>"$context"
	fi
done

if [[ $status == conflict ]]; then
	{
		for f in "${files[@]}"; do
			echo "===== CURRENT UPSTREAM $f at ${commit:0:12}"
			git -C "$src" show "FETCH_HEAD:$f" | head -c 120000
		done
		if [[ -n $previous && $previous != "$commit" ]] &&
			git -C "$src" fetch -q --depth=1 --filter=blob:none origin "$previous" 2>/dev/null; then
			echo "===== UPSTREAM CHANGES ${previous:0:12}..${commit:0:12} to these files"
			git -C "$src" diff "$previous" "$commit" -- "${files[@]}" | head -c 150000
		fi
	} >>"$context"
	{
		echo
		echo '<details><summary>git apply output</summary>'
		echo
		echo '```'
		grep -A40 '^===== git apply' "$context" | head -80
		echo '```'
		echo '</details>'
	} >>"$report"
fi

rm -rf "$src"
cat "$report"
if [[ -n ${GITHUB_OUTPUT:-} ]]; then
	echo "status=$status" >>"$GITHUB_OUTPUT"
	echo "skip=${skip[*]}" >>"$GITHUB_OUTPUT"
fi
