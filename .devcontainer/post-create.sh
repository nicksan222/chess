#!/usr/bin/env bash
set -euo pipefail

git config --local core.hooksPath .githooks
./tools/check
