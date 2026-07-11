#!/usr/bin/env bash
# lib-common.sh — shared helpers, path resolution, and lifecycle globals for the E2E harness.
#
# Sourced first by run-e2e.sh. Defines functions and declares the globals that the per-subsystem
# libraries and the EXIT-trap teardown all read/write. No logic runs at source time.
#
# Mirrors the proven helpers from scripts/run_invitation_terms_acceptance_web_e2e.sh
# (log/fail/on_error/run_with_timeout) so the E2E orchestration shares one logging and
# timeout convention across the project.

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
# Legacy Aplicatudo layout: <monorepo>/projects/aplicatudo/scripts/e2e
#   ROOT = Flutter app dir, MONOREPO_ROOT = monorepo root, E2E_WORKSPACE = ROOT/e2e_test
# Scaffolded plugin layout: <project>/e2e_test/scripts/e2e (via maestro-e2e --init)
#   ROOT = project root, MONOREPO_ROOT = project root, E2E_WORKSPACE = e2e_test/
_LIB_COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_SCRIPTS_PARENT="$(cd "${_LIB_COMMON_DIR}/../.." && pwd)"

if [[ "$(basename "$_SCRIPTS_PARENT")" == "e2e_test" ]]; then
  E2E_WORKSPACE="${E2E_WORKSPACE:-$_SCRIPTS_PARENT}"
  MONOREPO_ROOT="${MONOREPO_ROOT:-$(cd "${_SCRIPTS_PARENT}/.." && pwd)}"
  ROOT="${ROOT:-$MONOREPO_ROOT}"
else
  ROOT="${ROOT:-$_SCRIPTS_PARENT}"
  MONOREPO_ROOT="${MONOREPO_ROOT:-$(cd "${ROOT}/../.." && pwd)}"
  E2E_WORKSPACE="${E2E_WORKSPACE:-${ROOT}/e2e_test}"
fi
export ROOT MONOREPO_ROOT E2E_WORKSPACE

# ---------------------------------------------------------------------------
# Lifecycle globals (shared with teardown — see lib-teardown.sh)
# Tracked so cleanup() only stops what THIS run started, never a developer's
# unrelated emulator/Firebase.
# ---------------------------------------------------------------------------
FIREBASE_PID=""             # PID of the backgrounded firebase emulators:start
FIREBASE_PGID=""            # its process-group id (setsid) — killed as a group on teardown
STARTED_FIREBASE="false"    # guard: did this run start Firebase?
BOOTED_AVD="false"          # guard: did this run boot the AVD?
EMULATOR_PID=""             # PID of the launched emulator before a serial exists
AVD_SERIAL=""               # e.g. emulator-5554 — the device this run booted
SEED_TMP_DIR=""             # disposable copy of .firebase_initial_data (removed on teardown)
E2E_REUSE_BUILD="${E2E_REUSE_BUILD:-false}"  # --reuse-build skips APK/Functions rebuilds when present

# Resolved tool paths (filled by lib-preflight.sh).
ADB="${ADB:-}"
EMULATOR_BIN="${EMULATOR_BIN:-}"
MAESTRO_BIN="${MAESTRO_BIN:-}"
FIREBASE_BIN="${FIREBASE_BIN:-}"   # global firebase CLI (the repo's local install is broken)
ANDROID_SDK_FROM_ADB="${ANDROID_SDK_FROM_ADB:-}"  # SDK root derived from adb's path (emulator fallback)
TIMEOUT_BIN="${TIMEOUT_BIN:-timeout}"  # coreutils timeout (gtimeout on macOS); resolved in preflight

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
_PROGRESS_ACTIVE="false"

log() {
  if [[ "$_PROGRESS_ACTIVE" == "true" ]]; then
    printf '\n' >&2
    _PROGRESS_ACTIVE="false"
  fi
  printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" >&2
}

# log_progress CURRENT TOTAL MESSAGE — polling-loop ticker: rewrites one line on a TTY; on
# non-TTY output (CI/redirect, where \r is garbage) emits a full line every 10 ticks.
log_progress() {
  local current="$1" total="$2" message="$3"
  if [[ -t 2 ]]; then
    printf '\r\033[K[%s] %s (%s/%ss)' "$(date '+%H:%M:%S')" "$message" "$current" "$total" >&2
    _PROGRESS_ACTIVE="true"
  elif (( current == 1 || current % 10 == 0 )); then
    log "${message} (${current}/${total}s)."
  fi
}

fail() {
  log "ERROR: $*"
  exit 1
}

on_error() {
  log "ERROR: script failed at line $1 with exit code $2."
}

# ---------------------------------------------------------------------------
# run_with_timeout LABEL TIMEOUT_SECONDS CMD [ARGS...]
# Runs a command under a hard timeout; fails the script on timeout or non-zero exit.
# ---------------------------------------------------------------------------
run_with_timeout() {
  local label="$1"
  local timeout_seconds="$2"
  shift 2

  log "Starting ${label} (timeout: ${timeout_seconds}s)."

  set +e
  "$TIMEOUT_BIN" --kill-after=5s "${timeout_seconds}s" "$@"
  local exit_code="$?"
  set -e

  if [[ "$exit_code" -eq 124 || "$exit_code" -eq 137 ]]; then
    fail "${label} exceeded ${timeout_seconds}s and was terminated."
  fi

  if [[ "$exit_code" -ne 0 ]]; then
    fail "${label} failed with exit code ${exit_code}."
  fi

  log "Finished ${label}."
}
