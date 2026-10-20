#!/usr/bin/env bash
set -euo pipefail
repo_root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
build_root=$(mktemp -d "${TMPDIR:-/tmp}/ballonstranslator-pkg.XXXXXX")
git -C "$repo_root" archive --format=tar --prefix=ballonstranslator/ \
    --output="$build_root/ballonstranslator-source.tar" HEAD
cp "$repo_root/packaging/arch/PKGBUILD" "$build_root/"
cd "$build_root"
makepkg --noconfirm
printf '\nPackage directory: %s\n' "$build_root"
