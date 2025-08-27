#!/usr/bin/env bash
set -euo pipefail
echo "--- Redundancy scan (warn-only) ---"
tmp="$(mktemp)"
git ls-files > "$tmp"
# Use a rare delimiter `|~|` to avoid escaping headaches
awk -F/ '{print $NF"|~|"$0}' "$tmp" | sort | awk -F'\|~\|' '
  {count[$1]++; path[$1]=path[$1]?path[$1]"\n    "$2:$2}
  END{
    for(k in count){
      if(count[k]>1){
        print "DUP:", k;
        print path[k];
        print ""
      }
    }
  }'
rm -f "$tmp" || true
