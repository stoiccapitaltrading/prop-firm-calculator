#!/usr/bin/env bash
set -euo pipefail

# Scan only tracked files so vendored/build folders don't create noise.
if git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- . >/dev/null; then
  echo "❌ Merge conflict markers found in tracked files:"
  git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- .
  echo "\nResolve all markers before committing."
  exit 1
fi

echo "✅ No merge conflict markers found in tracked files."
