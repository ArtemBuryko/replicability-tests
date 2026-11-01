#!/usr/bin/env bash
# The envelope's one command — replicability test 01 · spec DRAFT v0.8 (SPEC.md).
#   ./run.sh <A|B> <run-id> [--dry | --test <model>]
# Needs, in the operator's shell: RT01_RUNS (a folder outside this repository); for a real run RT01_TEXT
# (the PDF), RT01_BRIEF (brief.md) and RT01_BUNDLE (the bundle's folder). Builder A runs under its plan,
# signed in by the operator in this run's sign-in phase (SPEC §5); builder B on the Gemini API, its key typed
# at this script's prompt, not echoed (SPEC §3b). The egress holds the plan's tokens and the key in the run's
# vault/, removed whenever this script exits; the builder holds stand-ins alone. --test <model>: builder B's
# test of its route — the dry run's inputs, another model in its settings (SPEC §7); not the dry run.
# Runs with the bash macOS ships (3.2).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
builder="${1:-}"; run="${2:-}"; mode="${3:-}"; test_model="${4:-}"
case "$builder" in A|B) ;; *) echo "usage: run.sh <A|B> <run-id> [--dry | --test <model>]" >&2; exit 2 ;; esac
case "$run" in ''|*[!A-Za-z0-9._-]*) echo "run-id: letters, digits, dot, dash, underscore" >&2; exit 2 ;; esac
case "$mode" in
  '')     kind=run ;;
  --dry)  kind=dry ;;
  --test) kind=test
          [ "$builder" = B ] || { echo "--test is builder B's alone" >&2; exit 2; }
          case "$test_model" in ''|*[!a-z0-9.-]*|gemini-4-argon) echo "--test needs another model: lower-case letters, digits, dot, dash" >&2; exit 2 ;; esac ;;
  *)      echo "the third argument can only be --dry or --test" >&2; exit 2 ;;
esac
[ "$kind" = test ] || [ -z "$test_model" ] || { echo "a model only with --test" >&2; exit 2; }
[ "$#" -le 4 ] || { echo "too many arguments" >&2; exit 2; }
: "${RT01_RUNS:?set RT01_RUNS to a folder outside this repository}"

sha() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
strsha() { if command -v sha256sum >/dev/null; then printf '%s' "$1" | sha256sum | cut -d' ' -f1; else printf '%s' "$1" | shasum -a 256 | cut -d' ' -f1; fi; }
TEXT_SHA=4d3f5e0a6f3ad7cff03ae0d58f7191aa4e2b87a85f319832900f2089a808be53
TEXT_NAME='EIOPA-BoS-26-198 - RFR Technical Documentation SII Review.pdf'
BUILDER_TAG=rt01-builder:local
EGRESS_IMAGE='mitmproxy/mitmproxy:12.3.1@sha256:2711066c855659b5af8b1dbb84494ed3eff69b42ece439c60b4fe09a2db829d4'

R="$RT01_RUNS/$run"
# Every run a run of its own, a restart too: a fresh folder, and no archive, console or sha256 of its id beside it (SPEC §6).
for f in "$R" "$RT01_RUNS/run-$run.tar.gz" "$RT01_RUNS/run-$run.console.txt" "$RT01_RUNS/run-$run.sha256"; do
  { [ ! -e "$f" ] && [ ! -L "$f" ]; } || { echo "$f exists: every run gets a fresh folder and a new id" >&2; exit 2; }
done
mkdir -p "$R"/in "$R"/work/return "$R"/logs "$R"/state/home/.gemini "$R"/state/codex "$R"/egress "$R"/ca "$R"/ca-public "$R"/vault
chmod 700 "$R/vault"
# The plan's real tokens and builder B's key stay in vault/ for this script's life alone.
trap 'rm -rf "$R/vault"' EXIT
trap 'exit 130' INT TERM HUP
say() { printf '%s\n' "$*" | tee -a "$R/console.txt"; }

if [ "$builder" = A ]; then
  MODEL=gpt-6-astra; ROUTE=chatgpt; MODELS=gpt-6-astra; CAP=
  CONFIG="$here/codex/config.toml"; TARGET=/state/codex/config.toml; CONFIG_DIR="$here/codex"
else
  MODEL=gemini-4-argon; ROUTE=gemini-api; MODELS=gemini-4-argon; CAP=55
  CONFIG="$here/gemini/settings.json"; TARGET=/state/home/.gemini/settings.json; CONFIG_DIR="$here/gemini"
fi

if [ "$kind" = run ]; then
  LIMIT=5h
  : "${RT01_TEXT:?}"; : "${RT01_BRIEF:?}"; : "${RT01_BUNDLE:?}"
  [ "$(sha "$RT01_TEXT")" = "$TEXT_SHA" ] || { echo "the text's sha256 is not the pin" >&2; exit 3; }
  cp "$RT01_BRIEF" "$R/in/brief.md"; cp "$RT01_TEXT" "$R/in/$TEXT_NAME"; cp -R "$RT01_BUNDLE" "$R/in/bundle"
else
  LIMIT=15m
  cp "$here/dry-run/brief.md" "$R/in/brief.md"
  awk 'BEGIN { for (i = 1; i <= 4000; i++) printf "padding line %04d — the envelope'"'"'s dry run carries no part of the text\n", i }' > "$R/in/padding.txt"
  [ "$builder" = B ] && CONFIG="$here/dry-run/gemini-settings.json"
fi
if [ "$kind" = test ]; then
  # The test's settings, made from the dry run's by one replacement: every "gemini-4-argon" becomes the test's model.
  n=$(grep -oF '"gemini-4-argon"' "$CONFIG" | wc -l | tr -d ' ')
  sed "s/\"gemini-4-argon\"/\"$test_model\"/g" "$CONFIG" > "$R/test-settings.json"
  m=$(grep -oF "\"$test_model\"" "$R/test-settings.json" | wc -l | tr -d ' ')
  if [ "$n" -lt 1 ] || [ "$n" != "$m" ] || grep -qF gemini-4-argon "$R/test-settings.json"; then
    echo "the test's settings: replacements $n, the test's model found $m" >&2; exit 3
  fi
  say "the test: model $test_model · its settings test-settings.json · sha256 $(sha "$R/test-settings.json") · made from $(basename "$CONFIG") · sha256 $(sha "$CONFIG") · replacements $n"
  CONFIG="$R/test-settings.json"; MODEL="$test_model"; MODELS="$test_model"
fi

if [ "$builder" = B ]; then
  # Builder B's key — typed here, not echoed, never an argument or a variable of the environment; written with
  # a stand-in into vault/ for the egress alone; the builder gets the stand-in (SPEC §3b).
  printf 'the Gemini API key for run %s — not echoed; held by the egress alone: ' "$run" > /dev/tty
  IFS= read -rs KEY < /dev/tty || KEY=
  printf '\n' > /dev/tty
  case "$KEY" in ''|*[!A-Za-z0-9._-]*) KEY=; say "the key: empty, or a character outside letters, digits, dot, dash and underscore — the run does not start"; exit 4 ;; esac
  if [ "${#KEY}" -lt 20 ] || [ "${#KEY}" -gt 200 ]; then KEY=; say "the key: its length outside 20 to 200 — the run does not start"; exit 4; fi
  STANDIN="rt01.api_key.$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')"
  KEY_SHA="$(strsha "$KEY")"
  ( umask 077; printf '{"real_by_standin":{"%s":"%s"},"standin_by_sha":{"%s":"%s"},"issued":{"api_key":1},"swapped":{}}\n' \
      "$STANDIN" "$KEY" "$KEY_SHA" "$STANDIN" > "$R/vault/vault.json" )
  KEY=; KEY_SHA=; unset KEY KEY_SHA
  ( umask 077; printf 'GEMINI_API_KEY=%s\n' "$STANDIN" > "$R/builder.env" )
  say "the key: typed at the prompt, held in vault/ for the egress alone · the builder's GEMINI_API_KEY its stand-in"
  say "the spend cap at the egress: \$$CAP a run — every generation refused once the sum of the answers' use reaches it (SPEC §3b)"
else
  : > "$R/builder.env"
fi

IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$BUILDER_TAG")"
# This run's own certificate authority: its key goes to the egress alone, its certificate to the builder.
docker run --rm --network none --user 1000:1000 -v "$R/ca:/ca" --entrypoint openssl "$IMAGE_ID" \
  req -x509 -newkey rsa:2048 -nodes -days 2 -subj "/CN=rt01 envelope $run" \
  -addext basicConstraints=critical,CA:TRUE -addext keyUsage=critical,keyCertSign,cRLSign \
  -keyout /ca/ca.key -out /ca/ca.crt 2>/dev/null
cat "$R/ca/ca.key" "$R/ca/ca.crt" > "$R/ca/mitmproxy-ca.pem"
cp "$R/ca/ca.crt" "$R/ca-public/mitmproxy-ca-cert.pem"

cat > "$R/run.env" <<EOF
RUN_DIR=$R
ENVELOPE_DIR=$here
BUILDER=$builder
RUN_ID=$run
RUN_KIND=$kind
TIME_LIMIT=$LIMIT
BUILDER_IMAGE_ID=$IMAGE_ID
EGRESS_IMAGE=$EGRESS_IMAGE
EGRESS_ROUTE=$ROUTE
EGRESS_MODELS=$MODELS
EGRESS_SPEND_CAP_USD=$CAP
MODEL=$MODEL
CONFIG_FILE=$CONFIG
CONFIG_TARGET=$TARGET
CONFIG_DIR=$CONFIG_DIR
EOF

P="rt01-$(printf '%s' "$run" | tr 'A-Z.' 'a-z-')"
dc() { docker compose -p "$P" -f "$here/compose.yaml" --env-file "$R/run.env" "$@"; }

if [ "$builder" = A ]; then
  # 1. The sign-in — the operator's, in this terminal, through the egress in its sign-in phase (SPEC §5).
  export EGRESS_PHASE=signin
  say "=== the sign-in · run $run · builder $builder · route $ROUTE · $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  dc up -d --wait egress 2>&1 | tee -a "$R/console.txt"
  set +e
  dc run --rm --no-deps builder signin
  s=$?
  set -e
  dc down >/dev/null 2>&1 || true
  [ "$s" = 0 ] || { say "the sign-in ended with status $s: the run does not start"; exit 4; }
  docker run --rm --network none --user 1000:1000 -v "$R:/r:ro" -v "$here/vault_check.py:/opt/vault_check.py:ro" \
    --entrypoint python3 "$IMAGE_ID" -I -B /opt/vault_check.py signin "$builder" 2>&1 | tee -a "$R/console.txt" \
    || { say "the stand-ins' check failed: the run does not start"; exit 4; }
else
  # 1. Builder B's key checked — no sign-in: one key in the vault, the builder given its stand-in (SPEC §3b).
  say "=== the key's check · run $run · builder $builder · route $ROUTE · $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  docker run --rm --network none --user 1000:1000 -v "$R:/r:ro" -v "$here/vault_check.py:/opt/vault_check.py:ro" \
    --entrypoint python3 "$IMAGE_ID" -I -B /opt/vault_check.py key "$builder" 2>&1 | tee -a "$R/console.txt" \
    || { say "the key's check failed: the run does not start"; exit 4; }
fi

# 2. The run — the builder through the egress in its run phase.
export EGRESS_PHASE=run
say "=== the run · $(date -u +%Y-%m-%dT%H:%M:%SZ)"
set +e
dc up --abort-on-container-exit --exit-code-from builder 2>&1 | tee -a "$R/console.txt"
set -e
dc down >/dev/null 2>&1 || true

# A return copied at the deadline is the return; the CLI's folder as it ended goes beside it, labelled (SPEC §6).
parts="work/return logs state egress"
if [ -d "$R/logs/return-at-deadline" ]; then
  mv "$R/work/return" "$R/work/return-after-deadline"
  mv "$R/logs/return-at-deadline" "$R/work/return"
  parts="work/return work/return-after-deadline logs state egress"
fi
( cd "$R" && tar -czf "$RT01_RUNS/run-$run.tar.gz" $parts )
H="$(sha "$RT01_RUNS/run-$run.tar.gz")"
# The archive scanned for the vault's real tokens, then the vault removed (SPEC §6).
set +e
docker run --rm --network none --user 1000:1000 -v "$R:/r:ro" -v "$RT01_RUNS/run-$run.tar.gz:/archive.tar.gz:ro" \
  -v "$here/vault_check.py:/opt/vault_check.py:ro" --entrypoint python3 "$IMAGE_ID" -I -B /opt/vault_check.py archive "$builder" \
  2>&1 | tee -a "$R/console.txt"
scan=${PIPESTATUS[0]}
set -e
rm -rf "$R/vault"
say "the vault: $([ -e "$R/vault" ] && echo 'NOT REMOVED' || echo removed)"
printf 'archive run-%s.tar.gz · %s bytes · sha256 %s\n' "$run" "$(wc -c < "$RT01_RUNS/run-$run.tar.gz" | tr -d ' ')" "$H" | tee -a "$R/console.txt"
cp "$R/console.txt" "$RT01_RUNS/run-$run.console.txt"
printf '%s  run-%s.tar.gz\n' "$H" "$run" > "$RT01_RUNS/run-$run.sha256"
exit "$scan"
