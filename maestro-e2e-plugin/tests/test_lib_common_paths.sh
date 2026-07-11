#!/usr/bin/env bash
# Validates lib-common.sh path resolution for legacy and scaffolded layouts.
set -euo pipefail

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$expected" != "$actual" ]]; then
    echo "FAIL: ${label}"
    echo "  expected: ${expected}"
    echo "  actual:   ${actual}"
    exit 1
  fi
}

source_paths() {
  # shellcheck disable=SC1090
  source "$1"
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

# Scaffolded layout: <project>/e2e_test/scripts/e2e
scaffold_project="${tmpdir}/myapp"
mkdir -p "${scaffold_project}/e2e_test/scripts/e2e"
cp maestro-e2e-plugin/scripts/e2e/lib-common.sh "${scaffold_project}/e2e_test/scripts/e2e/"
(
  cd "${scaffold_project}"
  source_paths "e2e_test/scripts/e2e/lib-common.sh"
  assert_eq "scaffold ROOT" "${scaffold_project}" "$ROOT"
  assert_eq "scaffold MONOREPO_ROOT" "${scaffold_project}" "$MONOREPO_ROOT"
  assert_eq "scaffold E2E_WORKSPACE" "${scaffold_project}/e2e_test" "$E2E_WORKSPACE"
)

# Legacy Aplicatudo layout: <monorepo>/projects/aplicatudo/scripts/e2e
legacy_monorepo="${tmpdir}/monorepo"
mkdir -p "${legacy_monorepo}/projects/aplicatudo/scripts/e2e"
cp maestro-e2e-plugin/scripts/e2e/lib-common.sh "${legacy_monorepo}/projects/aplicatudo/scripts/e2e/"
(
  cd "${legacy_monorepo}/projects/aplicatudo"
  source_paths "scripts/e2e/lib-common.sh"
  assert_eq "legacy ROOT" "${legacy_monorepo}/projects/aplicatudo" "$ROOT"
  assert_eq "legacy MONOREPO_ROOT" "${legacy_monorepo}" "$MONOREPO_ROOT"
  assert_eq "legacy E2E_WORKSPACE" "${legacy_monorepo}/projects/aplicatudo/e2e_test" "$E2E_WORKSPACE"
)

echo "PASS: lib-common path resolution"
