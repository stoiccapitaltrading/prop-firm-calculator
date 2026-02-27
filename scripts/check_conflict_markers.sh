#!/usr/bin/env bash
set -euo pipefail

if rg -n "^(<<<<<<<|=======|>>>>>>>)" .; then
  echo "❌ Merge conflict markers found. Resolve them before committing."
  exit 1
fi

echo "✅ No merge conflict markers found."
