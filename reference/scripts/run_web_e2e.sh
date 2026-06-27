#!/bin/bash
set -e

MY_TEST_TARGET="integration_test/modules/authentication/presentation/login_page/login_page_widget_test.dart"

flutter drive \
  --driver=test_driver/integration_test.dart \
  --target="$MY_TEST_TARGET" \
  -d chrome \
  --dart-define "IS_RUNNING_INTEGRATION_TESTS=true"
