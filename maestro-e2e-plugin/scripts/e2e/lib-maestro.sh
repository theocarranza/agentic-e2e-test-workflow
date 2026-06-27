#!/usr/bin/env bash
# lib-maestro.sh — Step 6: run the Maestro flows in e2e_test/ against the booted emulator.
#
# Invokes the locally vendored Maestro binary (resolved in preflight) by full path on the e2e_test/
# workspace, so config.yaml's flow glob discovers every module flow. Reports pass/fail via the exit
# code; the orchestrator's EXIT trap handles teardown regardless of result.
#
# Depends on lib-common.sh (log/fail/run_with_timeout, ROOT, MAESTRO_BIN/AVD_SERIAL).

E2E_WORKSPACE="${E2E_WORKSPACE:-${ROOT}/e2e_test}"
MAESTRO_TEST_TIMEOUT_SECONDS="${MAESTRO_TEST_TIMEOUT_SECONDS:-600}"

# ---------------------------------------------------------------------------
# Step 6: run all flows. Returns Maestro's exit code (0 = all passed).
# ---------------------------------------------------------------------------
run_maestro_flows() {
  [[ -n "$MAESTRO_BIN" ]] || fail "Maestro binary not resolved; run preflight first."
  [[ -d "$E2E_WORKSPACE" ]] || fail "Maestro workspace not found at ${E2E_WORKSPACE}."
  [[ -n "$AVD_SERIAL" ]] || fail "run_maestro_flows called before the emulator attached."

  # FLOW_FILTER: optional path to a single flow file (relative to E2E_WORKSPACE) for focused runs.
  # Unset or empty = run the full workspace. Revert to empty when done debugging.
  local _target="${E2E_WORKSPACE}"
  if [[ -n "${FLOW_FILTER:-}" ]]; then
    _target="${E2E_WORKSPACE}/${FLOW_FILTER}"
    log "FLOW_FILTER active — running only: ${_target}"
  fi

  log "Running Maestro flows in ${_target} on ${AVD_SERIAL}."

  MAESTRO_DRIVER_STARTUP_TIMEOUT="${MAESTRO_DRIVER_STARTUP_TIMEOUT:-120000}" \
  run_with_timeout \
    "Maestro test run" \
    "$MAESTRO_TEST_TIMEOUT_SECONDS" \
    "$MAESTRO_BIN" --device "$AVD_SERIAL" test "$_target"

  log "Maestro flows passed."
}
