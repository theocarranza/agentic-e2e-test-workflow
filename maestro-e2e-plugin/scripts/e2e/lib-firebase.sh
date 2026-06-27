#!/usr/bin/env bash
# lib-firebase.sh — Firebase Local Emulator Suite lifecycle for the E2E harness.
#
# Responsibilities:
#   - prekill_firebase_emulators : Step 2 (pre-clean) — kill strays bound to the test ports.
#   - ensure_functions_compiled  : Step 5 (part) — build Functions only if not already compiled.
#   - start_firebase_emulators   : Step 4 — import a DISPOSABLE copy of the golden seed and start
#                                  auth/functions/firestore/storage, never exporting on exit so the
#                                  committed .firebase_initial_data is never mutated.
#   - wait_for_auth_emulator     : Step 4 — block until the Auth emulator answers on 9099.
#
# Depends on lib-common.sh (log/fail/run_with_timeout, ROOT/MONOREPO_ROOT, FIREBASE_PID/PGID/
# STARTED_FIREBASE/SEED_TMP_DIR globals). Emulators MUST start from MONOREPO_ROOT (firebase.json lives
# there).

FIREBASE_PROJECT="${FIREBASE_PROJECT:-aplicatudo-dev}"
FIREBASE_LOG="${FIREBASE_LOG:-${ROOT}/.dart_tool/e2e-firebase.log}"
SEED_SRC="${SEED_SRC:-${MONOREPO_ROOT}/.firebase_initial_data}"
AUTH_EMULATOR_PORT="${AUTH_EMULATOR_PORT:-9099}"
FUNCTIONS_EMULATOR_PORT="${FUNCTIONS_EMULATOR_PORT:-5001}"
FIRESTORE_EMULATOR_PORT="${FIRESTORE_EMULATOR_PORT:-8080}"
# Storage uses the emulator default (firebase.json sets no port). Included in the pre-clean because
# the harness starts the storage emulator too.
STORAGE_EMULATOR_PORT="${STORAGE_EMULATOR_PORT:-9199}"
FIREBASE_READY_TIMEOUT_SECONDS="${FIREBASE_READY_TIMEOUT_SECONDS:-120}"
FUNCTIONS_BUILD_TIMEOUT_SECONDS="${FUNCTIONS_BUILD_TIMEOUT_SECONDS:-180}"
# Opt-in pre-clean of test ports. The dev's `firebase:start:no-hosting` shares these ports, so the
# harness and that command are mutually exclusive — see the infra doc.
E2E_PREKILL_PORTS="${E2E_PREKILL_PORTS:-true}"
E2E_FORCE_FUNCTIONS_BUILD="${E2E_FORCE_FUNCTIONS_BUILD:-false}"

# ---------------------------------------------------------------------------
# Step 2 (pre-clean): kill any process bound to a test port from a crashed prior run.
# Scoped to the four test ports the harness starts — never a blanket emulator kill.
# ---------------------------------------------------------------------------
prekill_firebase_emulators() {
  [[ "$E2E_PREKILL_PORTS" == "true" ]] || { log "Skipping Firebase port pre-clean (E2E_PREKILL_PORTS != true)."; return 0; }

  local port pids
  for port in "$AUTH_EMULATOR_PORT" "$FUNCTIONS_EMULATOR_PORT" "$FIRESTORE_EMULATOR_PORT" "$STORAGE_EMULATOR_PORT"; do
    if ! command -v lsof >/dev/null 2>&1; then
      log "lsof not available; skipping port pre-clean for ${port}."
      continue
    fi
    # Only LISTEN sockets — never a client connection. The Android emulator keeps a client socket
    # to the Functions port (10.0.2.2 -> host 5001); matching that would kill the emulator.
    pids="$(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      log "Pre-clean: killing stray listener(s) on test port ${port}: ${pids//$'\n'/ }."
      # shellcheck disable=SC2086
      kill ${pids} 2>/dev/null || true
    fi
  done
}

# ---------------------------------------------------------------------------
# Step 5 (part): build Functions by default. The Functions emulator needs projects/functions/lib/*.js.
# --reuse-build (or E2E_REUSE_BUILD=true) reuses the compiled lib when present.
# ---------------------------------------------------------------------------
ensure_functions_compiled() {
  local functions_dir="${MONOREPO_ROOT}/projects/functions"
  if [[ "$E2E_FORCE_FUNCTIONS_BUILD" != "true" && "$E2E_REUSE_BUILD" == "true" ]] && compgen -G "${functions_dir}/lib/*.js" >/dev/null 2>&1; then
    log "Reusing compiled Functions at ${functions_dir}/lib (--reuse-build)."
    return 0
  fi
  log "Building Functions."
  run_with_timeout \
    "Functions build" \
    "$FUNCTIONS_BUILD_TIMEOUT_SECONDS" \
    npm --prefix "$functions_dir" run build
}

# ---------------------------------------------------------------------------
# Step 4: start emulators against a disposable copy of the golden seed.
# The copy lives under .dart_tool/ (gitignored). No --export-on-exit, so neither
# the copy nor .firebase_initial_data is ever written back.
# ---------------------------------------------------------------------------
start_firebase_emulators() {
  [[ -d "$SEED_SRC" ]] || fail "Seed dataset not found at ${SEED_SRC}."

  mkdir -p "${ROOT}/.dart_tool"
  SEED_TMP_DIR="$(mktemp -d "${ROOT}/.dart_tool/e2e-seed.XXXXXX")"
  log "Copying golden seed to disposable dir ${SEED_TMP_DIR}."
  cp -a "${SEED_SRC}/." "${SEED_TMP_DIR}/"

  log "Starting Firebase emulators (auth,functions,firestore,storage) from ${MONOREPO_ROOT}."
  # setsid → fresh process group so teardown can kill the whole emulator tree (incl. the Java
  # children) by PGID. Run from the monorepo root where firebase.json lives. Uses the global
  # firebase CLI resolved in preflight (the repo's local install is broken).
  local firebase_bin="${FIREBASE_BIN:-firebase}"
  setsid bash -c "cd '${MONOREPO_ROOT}' && exec '${firebase_bin}' -P '${FIREBASE_PROJECT}' emulators:start \
    --only auth,functions,firestore,storage --import='${SEED_TMP_DIR}'" \
    >"$FIREBASE_LOG" 2>&1 &
  # Mark started and capture the PID before deriving the PGID, so teardown fires even if the
  # 'ps' below fails (process died instantly) — it falls back to FIREBASE_PID. The '|| true'
  # keeps pipefail/set -e from aborting on that same instant-death window.
  FIREBASE_PID="$!"
  STARTED_FIREBASE="true"
  FIREBASE_PGID="$(ps -o pgid= -p "$FIREBASE_PID" 2>/dev/null | tr -d ' ' || true)"
  log "Firebase emulators starting (pid ${FIREBASE_PID}, pgid ${FIREBASE_PGID:-?}). Log: ${FIREBASE_LOG}."
}

# ---------------------------------------------------------------------------
# Step 4: block until the Auth emulator is ready. Validates the response body is actually the
# Firebase Auth emulator (its root returns {"authEmulator":{"ready":true}}), so a stray service
# squatting on the port is not mistaken for readiness. Fails fast if the process dies first.
# ---------------------------------------------------------------------------
wait_for_auth_emulator() {
  log "Waiting for the Auth emulator on port ${AUTH_EMULATOR_PORT}."
  local elapsed response
  for ((elapsed = 1; elapsed <= FIREBASE_READY_TIMEOUT_SECONDS; elapsed++)); do
    response="$(curl -s "http://127.0.0.1:${AUTH_EMULATOR_PORT}/" 2>/dev/null || true)"
    if [[ "$response" == *authEmulator* ]]; then
      log "Auth emulator is ready on port ${AUTH_EMULATOR_PORT}."
      return 0
    fi
    if [[ -n "$FIREBASE_PID" ]] && ! kill -0 "$FIREBASE_PID" >/dev/null 2>&1; then
      fail "Firebase emulators exited before becoming ready. See ${FIREBASE_LOG} for details."
    fi
    log_progress "$elapsed" "$FIREBASE_READY_TIMEOUT_SECONDS" "Waiting for Auth emulator"
    sleep 1
  done
  fail "Auth emulator did not become ready on port ${AUTH_EMULATOR_PORT} within ${FIREBASE_READY_TIMEOUT_SECONDS}s. See ${FIREBASE_LOG}."
}
