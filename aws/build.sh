#!/usr/bin/env bash
# Builds the two Lambda packages in .aws-build/ without Docker:
#   api/     only portfolio/cloud (boto3 comes with the runtime)
#   worker/  the whole portfolio package + Linux wheels of its dependencies
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=.aws-build
PIP="${PIP:-.venv/bin/pip}"
rm -rf "$OUT" && mkdir -p "$OUT/api/portfolio" "$OUT/worker"

cp portfolio/__init__.py "$OUT/api/portfolio/"
cp -R portfolio/cloud "$OUT/api/portfolio/"

"$PIP" install --quiet --disable-pip-version-check \
  --platform manylinux2014_x86_64 --implementation cp --python-version 3.13 \
  --only-binary=:all: --target "$OUT/worker" -r aws/requirements-worker.txt
"$PIP" install --quiet --disable-pip-version-check --no-deps \
  --target "$OUT/worker" ppi-client==1.2.4 signalrcorePPI==0.9.2
cp -R portfolio "$OUT/worker/"

# trim: tests of the scientific stack and bytecode caches (~80 MB) so the
# unzipped package stays well under Lambda's 250 MB.
rm -rf "$OUT/worker/pandas/tests"
find "$OUT" -type d \( -name __pycache__ -o -path "*/numpy/*tests" \) -prune -exec rm -rf {} +
du -sh "$OUT/api" "$OUT/worker"
