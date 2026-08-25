#!/usr/bin/env bash
# Sets up sleeper-dash as a PRIVATE GitHub repo with the scheduled refresh
# working end to end. Run it from inside the sleeper-dash folder.
#
#   chmod +x setup.sh && ./setup.sh
#
# Requires the GitHub CLI, authenticated as you:
#   brew install gh && gh auth login

set -euo pipefail

REPO_NAME="${1:-sleeper-dash}"
SLEEPER_USER="${2:-ddillonn}"

command -v gh >/dev/null || { echo "gh not found. brew install gh, then gh auth login"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "not logged in. run: gh auth login"; exit 1; }

echo "==> local git repo"
[ -d .git ] || git init -b main -q
git add -A
git diff --staged --quiet || git commit -qm "sleeper dash: initial commit"

echo "==> creating PRIVATE repo: $REPO_NAME"
gh repo create "$REPO_NAME" --private --source=. --push

SLUG="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "==> repo is $SLUG"

echo "==> setting SLEEPER_USER variable to $SLEEPER_USER"
gh variable set SLEEPER_USER --body "$SLEEPER_USER"

echo "==> granting the workflow write access (so it can commit the snapshot)"
gh api -X PUT "repos/$SLUG/actions/permissions/workflow" \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=false >/dev/null

echo "==> kicking off the first refresh"
gh workflow run "refresh sleeper snapshot" || \
  echo "   (if that failed, run it from the Actions tab once)"

cat <<EOF

done.

  repo:     https://github.com/$SLUG  (private)
  actions:  https://github.com/$SLUG/actions
  schedule: 11:00 and 22:00 UTC daily

next:
  1. watch the first run. the job summary page is your gameday brief.
  2. deploy the UI at https://share.streamlit.io
     - main file: app.py
     - private repos work, you just authorize Streamlit to read this one
  3. locally:  pip install -r requirements.txt && streamlit run app.py

heads up: the committed snapshot is still DEMO data until that first
successful run overwrites it. if you see a player named "F. Filler",
the live pull has not landed yet.
EOF
