#!/usr/bin/env bash
# lib-emulator.sh — Android emulator (AVD) lifecycle for the E2E harness.
#
# Responsibilities:
#   - ensure_avd_running      : Step 3 — reuse/start the correct emulator for this run.
#   - capture_running_emulator: Step 3 — capture the serial in the parent shell after parallel boot.
#   - boot_avd                : Step 3 — boot the AVD (windowed) and capture its serial.
#   - wait_for_boot_completed : Step 3 — block until sys.boot_completed == 1.
#
# AVD selection is configurable + detectable: E2E_AVD_NAME if set, else reuse a running emulator or
# start the first entry of `emulator -list-avds`. No fixed name is assumed.
#
# Depends on lib-common.sh (log/fail, ADB/EMULATOR_BIN, BOOTED_AVD/AVD_SERIAL globals) and on
# preflight having resolved ADB + EMULATOR_BIN.

E2E_AVD_NAME="${E2E_AVD_NAME:-}"
EMULATOR_BOOT_TIMEOUT_SECONDS="${EMULATOR_BOOT_TIMEOUT_SECONDS:-180}"
# Extra emulator flags. The emulator runs windowed (a regular emulator, not headless); -no-snapshot
# gives a clean cold boot each run. Override EMULATOR_FLAGS to customize.
EMULATOR_FLAGS="${EMULATOR_FLAGS:--no-snapshot -no-boot-anim -gpu swiftshader_indirect}"

# ---------------------------------------------------------------------------
# Resolve the AVD name to boot: explicit override, else first listed AVD.
# ---------------------------------------------------------------------------
resolve_avd_name() {
  if [[ -n "$E2E_AVD_NAME" ]]; then
    echo "$E2E_AVD_NAME"
    return 0
  fi
  local first
  first="$("$EMULATOR_BIN" -list-avds 2>/dev/null | head -n 1)"
  [[ -n "$first" ]] || fail "No Android AVD found. Create one (e.g. 'avdmanager create avd -n e2e -k <system-image>') or set E2E_AVD_NAME."
  echo "$first"
}

# ---------------------------------------------------------------------------
# Find the first running Android emulator serial. This intentionally prefers an
# already-running emulator, regardless of AVD name, so local E2E runs can reuse a
# developer's active emulator instead of cycling it.
# ---------------------------------------------------------------------------
_first_running_emulator_serial() {
  local serial state fallback=""
  while read -r serial _; do
    [[ "$serial" == emulator-* ]] || continue
    state="$("$ADB" -s "$serial" get-state 2>/dev/null || true)"
    if [[ "$state" == "device" ]]; then
      echo "$serial"
      return 0
    fi
    [[ -z "$fallback" ]] && fallback="$serial"
  done < <("$ADB" devices 2>/dev/null | tail -n +2)
  if [[ -n "$fallback" ]]; then
    echo "$fallback"
    return 0
  fi
  return 1
}

# ---------------------------------------------------------------------------
# Find the serial (emulator-NNNN) of a running emulator whose AVD name matches.
# Emits nothing if not found.
# ---------------------------------------------------------------------------
_serial_for_avd() {
  local target="$1" serial avd_name
  while read -r serial _; do
    [[ "$serial" == emulator-* ]] || continue
    avd_name="$("$ADB" -s "$serial" emu avd name 2>/dev/null | head -n 1 | tr -d '\r' || true)"
    if [[ "$avd_name" == "$target" ]]; then
      echo "$serial"
      return 0
    fi
  done < <("$ADB" devices 2>/dev/null | tail -n +2)
  return 1
}

# ---------------------------------------------------------------------------
# Stop every running Android emulator except the optional serial to keep.
# Used only when the caller explicitly selected an AVD name.
# ---------------------------------------------------------------------------
_stop_running_emulators_except() {
  local keep_serial="${1:-}" serial
  while read -r serial _; do
    [[ "$serial" == emulator-* ]] || continue
    [[ -n "$keep_serial" && "$serial" == "$keep_serial" ]] && continue
    log "Stopping running Android emulator ${serial} before starting requested AVD '${E2E_AVD_NAME}'."
    "$ADB" -s "$serial" emu kill >/dev/null 2>&1 || true
  done < <("$ADB" devices 2>/dev/null | tail -n +2)
  sleep 2
}

# ---------------------------------------------------------------------------
# Step 3: use the explicit AVD when requested; otherwise reuse any running emulator, or boot the
# default AVD.
# ---------------------------------------------------------------------------
ensure_avd_running() {
  local serial
  if [[ -n "$E2E_AVD_NAME" ]]; then
    serial="$(_serial_for_avd "$E2E_AVD_NAME" || true)"
    _stop_running_emulators_except "$serial"
    if [[ -n "$serial" ]]; then
      log "Using requested Android emulator '${E2E_AVD_NAME}' at ${serial}."
      return 0
    fi
    boot_avd
    wait_for_boot_completed
    return 0
  fi

  serial="$(_first_running_emulator_serial || true)"
  if [[ -n "$serial" ]]; then
    log "Using already running Android emulator ${serial}."
    return 0
  fi

  boot_avd
  wait_for_boot_completed
}

# ---------------------------------------------------------------------------
# Step 3: capture the selected emulator serial in the parent shell after the
# parallel startup phase. Fails if no emulator is attached.
# ---------------------------------------------------------------------------
capture_running_emulator() {
  AVD_SERIAL="$(_first_running_emulator_serial || true)"
  [[ -n "$AVD_SERIAL" ]] || fail "No running Android emulator found after startup."
  log "Using Android emulator ${AVD_SERIAL}."
}

# ---------------------------------------------------------------------------
# Step 3: boot the AVD (windowed). Captures AVD_SERIAL and sets BOOTED_AVD.
# ---------------------------------------------------------------------------
boot_avd() {
  local avd
  avd="$(resolve_avd_name)"
  log "Booting AVD '${avd}' (${EMULATOR_FLAGS})."

  # shellcheck disable=SC2086
  nohup setsid "$EMULATOR_BIN" -avd "$avd" ${EMULATOR_FLAGS} >"${ROOT}/.dart_tool/e2e-emulator.log" 2>&1 < /dev/null &
  # Capture the launch PID and mark BOOTED before the attach loop, so the run knows it started the
  # emulator even if it hangs and never registers a serial with adb.
  EMULATOR_PID="$!"
  BOOTED_AVD="true"

  # Wait for the device to attach, then capture its serial.
  log "Waiting for the emulator to attach."
  local elapsed
  for ((elapsed = 1; elapsed <= EMULATOR_BOOT_TIMEOUT_SECONDS; elapsed++)); do
    AVD_SERIAL="$(_serial_for_avd "$avd" || true)"
    [[ -n "$AVD_SERIAL" ]] && break
    sleep 1
  done
  [[ -n "$AVD_SERIAL" ]] || fail "Emulator '${avd}' did not attach within ${EMULATOR_BOOT_TIMEOUT_SECONDS}s. See ${ROOT}/.dart_tool/e2e-emulator.log."
  log "Emulator attached as ${AVD_SERIAL}."
}

# ---------------------------------------------------------------------------
# Step 3: block until the OS reports boot_completed.
# ---------------------------------------------------------------------------
wait_for_boot_completed() {
  [[ -n "$AVD_SERIAL" ]] || fail "wait_for_boot_completed called before the emulator attached."
  log "Waiting for boot_completed on ${AVD_SERIAL}."

  local elapsed booted
  for ((elapsed = 1; elapsed <= EMULATOR_BOOT_TIMEOUT_SECONDS; elapsed++)); do
    # The device is 'offline' right after attaching, so getprop fails for the first seconds. Guard
    # the substitution (|| true) so pipefail/set -e doesn't abort — the loop just retries.
    booted="$("$ADB" -s "$AVD_SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' | tr -d ' ' || true)"
    if [[ "$booted" == "1" ]]; then
      log "Emulator ${AVD_SERIAL} finished booting."
      "$ADB" -s "$AVD_SERIAL" shell input keyevent 82 >/dev/null 2>&1 || true  # dismiss lock screen
      return 0
    fi
    log_progress "$elapsed" "$EMULATOR_BOOT_TIMEOUT_SECONDS" "Waiting for boot_completed"
    sleep 1
  done
  fail "Emulator ${AVD_SERIAL} did not reach boot_completed within ${EMULATOR_BOOT_TIMEOUT_SECONDS}s."
}
