#!/usr/bin/env bash
# lib-preflight.sh — Step 1: tool detection + local Maestro vendoring.
#
# System dependencies (adb, fvm, firebase, Java 17+) are DETECTED ONLY — if missing the harness
# stops with install guidance, it never mutates the developer's global environment. Maestro is the
# one tool the harness PROVISIONS, into a disposable project-local dir (.dart_tool/maestro),
# mirroring the chromedriver vendoring pattern in run_invitation_terms_acceptance_web_e2e.sh.
#
# Depends on lib-common.sh (log/fail/run_with_timeout, ROOT, ADB/EMULATOR_BIN/MAESTRO_BIN globals).

# Pinned Maestro release. Tag scheme is cli-X.Y.Z; the zip extracts to maestro/bin/maestro.
# Pin a real, tested version — never 'latest' in a committed script.
MAESTRO_VERSION="${MAESTRO_VERSION:-2.6.0}"
MAESTRO_ROOT="${MAESTRO_ROOT:-${ROOT}/.dart_tool/maestro}"
MAESTRO_DOWNLOAD_TIMEOUT_SECONDS="${MAESTRO_DOWNLOAD_TIMEOUT_SECONDS:-120}"
MAESTRO_VERSION_MARKER="${MAESTRO_ROOT}/.version"

MIN_JAVA_MAJOR="${MIN_JAVA_MAJOR:-17}"

# ---------------------------------------------------------------------------
# adb / emulator resolution — PATH first, then ANDROID_HOME / ANDROID_SDK_ROOT.
# No hardcoded absolute path.
# ---------------------------------------------------------------------------
_resolve_sdk_tool() {
  # _resolve_sdk_tool <tool-name> <sdk-subpath>
  local tool="$1" subpath="$2"
  if command -v "$tool" >/dev/null 2>&1; then
    command -v "$tool"
    return 0
  fi
  # Search ANDROID_HOME / ANDROID_SDK_ROOT, plus the SDK root derived from adb's own path — so a
  # sibling tool (emulator) resolves even when neither env var is exported, as long as adb is found.
  local base
  for base in "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}" "${ANDROID_SDK_FROM_ADB:-}"; do
    if [[ -n "$base" && -x "${base}/${subpath}" ]]; then
      echo "${base}/${subpath}"
      return 0
    fi
  done
  return 1
}

detect_adb() {
  ADB="$(_resolve_sdk_tool adb platform-tools/adb)" \
    || fail "adb not found. Install the Android SDK platform-tools and set ANDROID_HOME, or add adb to PATH."
  # Derive the SDK root from adb's resolved location (<sdk>/platform-tools/adb), so sibling tools
  # like the emulator are findable even when ANDROID_HOME / ANDROID_SDK_ROOT aren't exported.
  local resolved_adb
  resolved_adb="$(readlink -f "$ADB" 2>/dev/null || echo "$ADB")"
  ANDROID_SDK_FROM_ADB="$(cd "$(dirname "$resolved_adb")/.." && pwd 2>/dev/null || echo '')"
  log "Using adb at ${ADB}."
}

ensure_adb_server() {
  log "Starting adb server."
  "$ADB" start-server >/dev/null \
    || fail "adb server failed to start. Run '${ADB} start-server' manually and check adb permissions."
}

detect_emulator() {
  EMULATOR_BIN="$(_resolve_sdk_tool emulator emulator/emulator)" \
    || fail "Android 'emulator' not found. Install the Android SDK emulator package and set ANDROID_HOME, or add it to PATH."
  log "Using emulator at ${EMULATOR_BIN}."
}

detect_timeout() {
  # run_with_timeout depends on coreutils 'timeout' (named 'gtimeout' on macOS via Homebrew
  # coreutils). Resolve it before anything uses run_with_timeout; fail with guidance if absent.
  if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_BIN="timeout"
  elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_BIN="gtimeout"
  else
    fail "'timeout' not found. Install coreutils (Linux: usually preinstalled; macOS: 'brew install coreutils' provides 'gtimeout')."
  fi
  log "Using timeout at $(command -v "$TIMEOUT_BIN")."
}

detect_fvm() {
  command -v fvm >/dev/null 2>&1 \
    || fail "fvm not found. Install Flutter Version Management (https://fvm.app/) and run 'fvm install' in projects/aplicatudo."
  log "Using fvm at $(command -v fvm)."
}

detect_firebase() {
  # Use the GLOBAL firebase CLI, not the repo's local devDependency: the local firebase-tools
  # (v13.13.0) install in this monorepo is broken (its bin errors out and lib/templates is missing),
  # so 'npx firebase' is unreliable. Detect the global CLI on PATH; do not provision it.
  if ! command -v firebase >/dev/null 2>&1; then
    fail "firebase CLI not found on PATH. Install firebase-tools globally (npm i -g firebase-tools, or the standalone installer from https://firebase.google.com/docs/cli)."
  fi
  FIREBASE_BIN="$(command -v firebase)"
  log "Using firebase at ${FIREBASE_BIN}."
}

detect_java() {
  command -v java >/dev/null 2>&1 \
    || fail "Java not found. Maestro requires JDK ${MIN_JAVA_MAJOR}+. Install a JDK and set JAVA_HOME."

  # Parse the major version from `java -version` (handles "1.8.0" → 8 and "21.0.11" → 21).
  local version_line major
  version_line="$(java -version 2>&1 | head -1)"
  major="$(printf '%s' "$version_line" | sed -E 's/.*version "([0-9]+)(\.([0-9]+))?.*/\1 \3/' | awk '{ if ($1 == 1) print $2; else print $1 }')"

  if [[ -z "$major" || ! "$major" =~ ^[0-9]+$ ]]; then
    fail "Could not parse Java version from: ${version_line}. Maestro requires JDK ${MIN_JAVA_MAJOR}+."
  fi
  if (( major < MIN_JAVA_MAJOR )); then
    fail "Java ${major} found but Maestro requires JDK ${MIN_JAVA_MAJOR}+. Install a newer JDK and set JAVA_HOME."
  fi
  log "Java ${major} detected (>= ${MIN_JAVA_MAJOR})."

  # Maestro requires JAVA_HOME. If unset, derive it from the java binary (convenience — does not
  # mutate the developer's shell profile, only this process's environment).
  if [[ -z "${JAVA_HOME:-}" ]]; then
    local java_bin resolved
    java_bin="$(command -v java)"
    resolved="$(readlink -f "$java_bin" 2>/dev/null || echo "$java_bin")"
    export JAVA_HOME="$(cd "$(dirname "$resolved")/.." && pwd)"
    log "JAVA_HOME was unset; derived JAVA_HOME=${JAVA_HOME} for this run."
  else
    log "Using JAVA_HOME=${JAVA_HOME}."
  fi
}

# ---------------------------------------------------------------------------
# Maestro vendoring (mirror ensure_chromedriver): resolve the binary in the
# disposable project dir; (re)download + extract on miss or version mismatch;
# reuse otherwise; echo the full path on stdout. All logs go to stderr.
# ---------------------------------------------------------------------------
_resolve_maestro_binary() {
  find "$MAESTRO_ROOT" -path '*/maestro/bin/maestro' -type f 2>/dev/null | head -n 1
}

ensure_maestro() {
  mkdir -p "$MAESTRO_ROOT"

  local maestro_bin installed_version
  maestro_bin="$(_resolve_maestro_binary)"
  installed_version="$(cat "$MAESTRO_VERSION_MARKER" 2>/dev/null || echo '')"

  if [[ -z "$maestro_bin" || "$installed_version" != "$MAESTRO_VERSION" ]]; then
    log "Installing Maestro ${MAESTRO_VERSION} into ${MAESTRO_ROOT}."
    rm -rf "$MAESTRO_ROOT"
    mkdir -p "$MAESTRO_ROOT"
    local url="https://github.com/mobile-dev-inc/Maestro/releases/download/cli-${MAESTRO_VERSION}/maestro.zip"
    run_with_timeout \
      "Maestro download" \
      "$MAESTRO_DOWNLOAD_TIMEOUT_SECONDS" \
      curl -fsSL -o "${MAESTRO_ROOT}/maestro.zip" "$url"
    ( cd "$MAESTRO_ROOT" && unzip -q maestro.zip && rm -f maestro.zip ) \
      || fail "Failed to extract Maestro zip into ${MAESTRO_ROOT}."
    printf '%s\n' "$MAESTRO_VERSION" >"$MAESTRO_VERSION_MARKER"
    maestro_bin="$(_resolve_maestro_binary)"
  else
    log "Reusing Maestro ${MAESTRO_VERSION} at ${maestro_bin}."
  fi

  [[ -n "$maestro_bin" ]] || fail "Could not resolve the Maestro binary after install."
  [[ -x "$maestro_bin" ]] || chmod +x "$maestro_bin"
  echo "$maestro_bin"
}

# ---------------------------------------------------------------------------
# preflight_detect_tools — run every detection + vendor Maestro. Populates the
# ADB / EMULATOR_BIN / MAESTRO_BIN globals from lib-common.sh.
# ---------------------------------------------------------------------------
preflight_detect_tools() {
  log "Preflight: detecting tools."
  detect_timeout   # first — run_with_timeout (used below by ensure_maestro) depends on it
  detect_adb
  ensure_adb_server
  detect_emulator
  detect_fvm
  detect_firebase
  detect_java
  MAESTRO_BIN="$(ensure_maestro)"
  log "Preflight complete. Maestro at ${MAESTRO_BIN}."
}
