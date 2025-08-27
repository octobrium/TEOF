#!/usr/bin/env bash
set -euo pipefail
branch="$(git for-each-ref 'refs/heads/autoprops/*' --sort=-committerdate --format='%(refname:short)' | head -n1)"
if [ -z "$branch" ]; then
  echo "No local autoprops/* branch found. Run tools/promote-doc.sh first."; exit 1
fi
echo "Pushing $branch ..."
git push -u origin "$branch"
echo "✓ Pushed $branch"
echo "Next: open the PR on GitHub and add label: auto-merge-docs"
