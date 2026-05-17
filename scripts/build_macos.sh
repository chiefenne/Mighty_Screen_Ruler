#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

APP_NAME="Mighty_Screen_Ruler"
CONDA_ENV="${CONDA_ENV:-ruler}"
DIST_DIR="dist/macos-app"
STAGING_DIR="build/release-staging"
RELEASE_DIR="release/macos"
RELEASE_ZIP="$RELEASE_DIR/${APP_NAME}-macos-x86_64.zip"

echo "Running tests in conda env: $CONDA_ENV"
conda run -n "$CONDA_ENV" python -m unittest discover -s tests

echo "Cleaning previous macOS build output"
rm -rf "$DIST_DIR" "$STAGING_DIR" "$RELEASE_ZIP"
mkdir -p "$DIST_DIR" "$STAGING_DIR" "$RELEASE_DIR"

echo "Building macOS app with Nuitka"
conda run -n "$CONDA_ENV" python -m nuitka \
  --mode=app-dist \
  --enable-plugin=pyside6 \
  --output-dir="$DIST_DIR" \
  --output-filename="$APP_NAME" \
  --output-folder-name="$APP_NAME" \
  --macos-app-name="$APP_NAME" \
  --macos-app-version=1.0 \
  Mighty_Screen_Ruler.py

APP_PATH="$DIST_DIR/${APP_NAME}.app"
if [[ ! -d "$APP_PATH" ]]; then
  echo "Expected app bundle not found: $APP_PATH" >&2
  exit 1
fi

echo "Staging app bundle"
ditto "$APP_PATH" "$STAGING_DIR/${APP_NAME}.app"

echo "Creating release ZIP: $RELEASE_ZIP"
(
  cd "$STAGING_DIR"
  ditto -c -k --sequesterRsrc --keepParent "${APP_NAME}.app" "$REPO_ROOT/$RELEASE_ZIP"
)

echo "Built $RELEASE_ZIP"
