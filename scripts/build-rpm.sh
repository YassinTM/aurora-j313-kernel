#!/usr/bin/env bash
# Build kernel-aurora-j313 in a Fedora container, from the repository root:
#   docker run ... registry.fedoraproject.org/fedora:44 bash scripts/build-rpm.sh
# Env: J313_RELEASE (default 0), SKIP_PATCHES (space-separated names).
# Output: out/rpms/*.rpm
set -euo pipefail
cd "$(dirname "$0")/.."

dnf -y -q install rpm-build dnf5-plugins python3 curl
pin() { python3 -I -c 'import json,sys; print(json.load(open("upstream.json"))[sys.argv[1]])' "$1"; }
commit=$(pin kernel_commit)
top=$PWD/out/rpmbuild spec=$PWD/out/rpmbuild/SPECS/kernel-aurora-j313.spec
rm -rf out && mkdir -p "$top/SOURCES" "$top/SPECS" out/rpms

tarball=$top/SOURCES/linux-$commit.tar.gz
curl -fsSL --retry 3 -o "$tarball" "https://codeload.github.com/aurora-silicon/linux/tar.gz/$commit"
echo "$(pin kernel_sha256)  $tarball" | sha256sum -c -
cp aurora/config aurora/fedora.config aurora/validate-config.py config/j313.config "$top/SOURCES/"

patchlines=$top/patchlines n=0
: >"$patchlines"
for p in patches/*.patch; do
	name=$(basename "$p")
	if [[ " ${SKIP_PATCHES:-} " == *" $name "* ]]; then
		echo "Leaving out $name (already upstream)"
		continue
	fi
	cp "$p" "$top/SOURCES/"
	echo "Patch$((n += 1)): $name" >>"$patchlines"
done

sed -e "s/@KERNEL_COMMIT@/$commit/" -e "s/@VERSION@/$(pin version)/g" \
	-e "s/@AURORA_RELEASE@/$(pin aurora_release)/g" -e "s/@J313_RELEASE@/${J313_RELEASE:-0}/g" \
	-e "s/@DATE@/$(LC_ALL=C date -u '+%a %b %d %Y')/" \
	-e "/^@PATCHES@$/{r $patchlines" -e 'd}' kernel-aurora-j313.spec.in >"$spec"
grep -E '^(Version|Release|Patch[0-9]+):' "$spec"

dnf -y -q builddep "$spec"
rpmbuild -bb --define "_topdir $top" --define "_smp_mflags -j$(nproc)" "$spec"
cp "$top"/RPMS/aarch64/*.rpm out/rpms/
ls -l out/rpms
