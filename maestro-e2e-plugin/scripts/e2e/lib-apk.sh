#!/usr/bin/env bash
# lib-apk.sh — Step 5: build the local-flavor APK and install it on the booted emulator.
#
# The `local` flavor (applicationIdSuffix .local → life.bhave.aplicatudo.local) plus the default
# (empty) ENV_NAME loads the `dotenv` file (ENVIRONMENT=local), which makes the app target the
# Firebase emulators on 10.0.2.2. No dart-define is needed. Debug build is used for speed and to
# avoid release signing.
#
# Depends on lib-common.sh (log/fail/run_with_timeout, ROOT, ADB/AVD_SERIAL).

APK_BUILD_TYPE="${APK_BUILD_TYPE:-debug}"  # debug | release
APK_PATH="${APK_PATH:-${ROOT}/build/app/outputs/flutter-apk/app-local-${APK_BUILD_TYPE}.apk}"
APK_APP_ID="${APK_APP_ID:-life.bhave.aplicatudo.local}"
APK_BUILD_TIMEOUT_SECONDS="${APK_BUILD_TIMEOUT_SECONDS:-600}"
APK_INSTALL_TIMEOUT_SECONDS="${APK_INSTALL_TIMEOUT_SECONDS:-180}"
# Builds by default. --reuse-build (or E2E_REUSE_BUILD=true) reuses an existing APK when present.
E2E_FORCE_APK="${E2E_FORCE_APK:-false}"

# ---------------------------------------------------------------------------
# Step 5: build the local-flavor APK (reuse only when explicitly requested).
# ---------------------------------------------------------------------------
build_local_apk() {
  if [[ "$E2E_FORCE_APK" != "true" && "$E2E_REUSE_BUILD" == "true" && -f "$APK_PATH" ]]; then
    log "Reusing existing APK at ${APK_PATH} (--reuse-build)."
    return 0
  fi

  local build_flag="--${APK_BUILD_TYPE}"
  log "Building local-flavor APK (${APK_BUILD_TYPE})."
  run_with_timeout \
    "Flutter APK build" \
    "$APK_BUILD_TIMEOUT_SECONDS" \
    fvm flutter build apk --flavor local "$build_flag"

  [[ -f "$APK_PATH" ]] || fail "APK build reported success but ${APK_PATH} is missing."
  log "Built APK at ${APK_PATH}."
}

# ---------------------------------------------------------------------------
# Step 5: install the APK on the booted emulator.
# ---------------------------------------------------------------------------
install_apk() {
  [[ -n "$AVD_SERIAL" ]] || fail "install_apk called before the emulator attached."
  [[ -f "$APK_PATH" ]] || fail "APK not found at ${APK_PATH}; build it first."

  log "Installing ${APK_PATH} on ${AVD_SERIAL}."
  run_with_timeout \
    "APK install" \
    "$APK_INSTALL_TIMEOUT_SECONDS" \
    "$ADB" -s "$AVD_SERIAL" install -r "$APK_PATH"
  log "Installed ${APK_APP_ID} on ${AVD_SERIAL}."
}
