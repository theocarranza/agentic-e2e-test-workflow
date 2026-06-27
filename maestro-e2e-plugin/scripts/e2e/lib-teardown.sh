#!/usr/bin/env bash
# lib-teardown.sh — Step 7: cleanup(), installed by run-e2e.sh as `trap cleanup EXIT`.
#
# Runs on every exit (success OR failure). Idempotent, stops Firebase started by this run, and leaves
# the Android emulator running for developer reuse.
#
# Depends on lib-common.sh (log, ADB, FIREBASE_PGID/STARTED_FIREBASE, BOOTED_AVD/AVD_SERIAL,
# SEED_TMP_DIR).

FIREBASE_TERM_GRACE_SECONDS="${FIREBASE_TERM_GRACE_SECONDS:-3}"

cleanup() {
  local exit_code="$?"
  log "Teardown: stopping services this run started."

  # --- Firebase: kill the whole process group (setsid) so the Java emulator children die too.
  # Fall back to the single PID if the PGID was never captured (e.g. instant-death window). ---
  if [[ "$STARTED_FIREBASE" == "true" ]]; then
    if [[ -n "$FIREBASE_PGID" ]]; then
      log "Stopping Firebase emulators (pgid ${FIREBASE_PGID})."
      kill -TERM "-${FIREBASE_PGID}" 2>/dev/null || true
      sleep "$FIREBASE_TERM_GRACE_SECONDS"
      kill -KILL "-${FIREBASE_PGID}" 2>/dev/null || true
    elif [[ -n "$FIREBASE_PID" ]]; then
      log "Stopping Firebase (pid ${FIREBASE_PID}; no pgid captured)."
      kill -TERM "$FIREBASE_PID" 2>/dev/null || true
      sleep "$FIREBASE_TERM_GRACE_SECONDS"
      kill -KILL "$FIREBASE_PID" 2>/dev/null || true
    fi
  fi

  if [[ -n "$AVD_SERIAL" || "$BOOTED_AVD" == "true" ]]; then
    log "Leaving Android emulator running."
  fi

  # --- Disposable seed copy. ---
  if [[ -n "$SEED_TMP_DIR" && -d "$SEED_TMP_DIR" ]]; then
    log "Removing disposable seed ${SEED_TMP_DIR}."
    rm -rf "$SEED_TMP_DIR"
  fi

  log "Teardown complete (exit ${exit_code})."
}
