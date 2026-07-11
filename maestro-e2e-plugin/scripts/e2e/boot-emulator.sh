#!/usr/bin/env bash
# boot-emulator.sh — MCP entry point to ensure an Android emulator is running.
#
# lib-emulator.sh is a sourced library; invoking it directly is a no-op. This script
# runs preflight detection and boots or reuses an emulator for Maestro MCP tools.

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=lib-common.sh
source "${_SCRIPT_DIR}/lib-common.sh"
# shellcheck source=lib-preflight.sh
source "${_SCRIPT_DIR}/lib-preflight.sh"
# shellcheck source=lib-emulator.sh
source "${_SCRIPT_DIR}/lib-emulator.sh"

preflight_detect_tools
ensure_avd_running
