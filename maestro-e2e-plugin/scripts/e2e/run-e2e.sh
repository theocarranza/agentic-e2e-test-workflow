#!/usr/bin/env bash
# run-e2e.sh — unified E2E orchestrator for the Aplicatudo Flutter app.
#
# Entry point behind `npm run test:e2e:android`. Runs the full Maestro-on-Android lifecycle over the
# Firebase Local Emulator Suite, fully unattended, and tears Firebase down on exit (success OR
# failure). The Android emulator is reused when already running and left running at the end:
#
#   1. preflight        — detect adb/emulator/fvm/firebase/Java 17+; vendor Maestro locally.
#   2. teardown prévio  — kill strays on Firebase test ports from a crashed prior run.
#   3. parallel startup — build APK, build Functions, reuse/boot Android emulator.
#   4. firebase         — copy the golden seed to a disposable dir, start the emulators, wait for Auth.
#   5. apk              — install the local-flavor APK.
#   6. maestro          — run the flows in e2e_test/, reporting pass/fail.
#   7. teardown final   — EXIT trap: stop Firebase (by process group), remove the seed.
#
# The committed golden seed (.firebase_initial_data) is never mutated — emulators import a disposable
# copy with no --export-on-exit.

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source order matters: lib-common declares the shared globals the other libs and the EXIT trap read.
# shellcheck source=lib-common.sh
source "${_SCRIPT_DIR}/lib-common.sh"
# shellcheck source=lib-preflight.sh
source "${_SCRIPT_DIR}/lib-preflight.sh"
# shellcheck source=lib-firebase.sh
source "${_SCRIPT_DIR}/lib-firebase.sh"
# shellcheck source=lib-emulator.sh
source "${_SCRIPT_DIR}/lib-emulator.sh"
# shellcheck source=lib-apk.sh
source "${_SCRIPT_DIR}/lib-apk.sh"
# shellcheck source=lib-maestro.sh
source "${_SCRIPT_DIR}/lib-maestro.sh"
# shellcheck source=lib-teardown.sh
source "${_SCRIPT_DIR}/lib-teardown.sh"

trap 'on_error "$LINENO" "$?"' ERR
trap cleanup EXIT

parse_args() {
  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --reuse-build)
        E2E_REUSE_BUILD="true"
        ;;
      --avd-name)
        shift
        [[ "$#" -gt 0 && -n "$1" ]] || fail "--avd-name requires an AVD name."
        E2E_AVD_NAME="$1"
        ;;
      --avd-name=*)
        E2E_AVD_NAME="${1#--avd-name=}"
        [[ -n "$E2E_AVD_NAME" ]] || fail "--avd-name requires an AVD name."
        ;;
      *)
        fail "Unknown argument: $1"
        ;;
    esac
    shift
  done
}

run_parallel_startup() {
  local emulator_phase_pid functions_build_pid apk_build_pid status=0

  log "Starting parallel setup: Android emulator, Functions build, Aplicatudo build."
  ensure_avd_running &
  emulator_phase_pid="$!"
  ensure_functions_compiled &
  functions_build_pid="$!"
  build_local_apk &
  apk_build_pid="$!"

  if ! wait "$emulator_phase_pid"; then
    status=1
  fi
  if ! wait "$functions_build_pid"; then
    status=1
  fi
  if ! wait "$apk_build_pid"; then
    status=1
  fi

  [[ "$status" -eq 0 ]] || fail "Parallel setup failed."
  capture_running_emulator
  wait_for_boot_completed
  log "Parallel setup completed."
}

main() {
  parse_args "$@"
  log "E2E run starting."

  # 1. Preflight (also resolves ADB/EMULATOR_BIN/MAESTRO_BIN).
  preflight_detect_tools

  # 2. Teardown prévio — clean Firebase ports before starting anything.
  prekill_firebase_emulators

  # 3. Parallel startup: Android emulator + Aplicatudo build + Functions build.
  run_parallel_startup

  # 4. Firebase emulators (disposable seed import), after Functions have been rebuilt.
  start_firebase_emulators
  wait_for_auth_emulator

  # 5. App under test.
  install_apk

  # 6. Run the flows. A failure here propagates a non-zero exit; the EXIT trap still tears down.
  run_maestro_flows

  log "E2E run completed successfully."
}

main "$@"
