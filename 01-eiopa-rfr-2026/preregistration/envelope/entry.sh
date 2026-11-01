#!/bin/bash
# The envelope's entrypoint in the builder container — replicability test 01 · spec DRAFT v0.12 (SPEC.md §3b, §4.2, §5, §6).
# `entry.sh signin`: builder A's sign-in, the operator's, through the egress in its sign-in phase. Otherwise: the
# launch print, then the CLI under its time limit, counted from the print's first second; at the deadline the
# return copied and hashed before any grace; then its exit status. Never prints a token's or a key's value.
set -uo pipefail
L=/logs
mkdir -p /work/return "$HOME" "$CODEX_HOME"
cat /etc/ssl/certs/ca-certificates.crt /ca/mitmproxy-ca-cert.pem > /state/ca-bundle.pem

case "$BUILDER" in
  A) CONFIG="$CODEX_HOME/config.toml"; CRED="$CODEX_HOME/auth.json" ;;
  B) CONFIG="$HOME/.gemini/settings.json"; CRED=; export GEMINI_EXP=/envelope/config/experiments.json ;;
  *) echo "BUILDER must be A or B"; exit 2 ;;
esac

if [ "${1:-}" = signin ]; then
  # The operator's sign-in, once per run, before the run: the tokens the vendor answers stay in the egress's
  # vault; the credential file gets stand-ins (SPEC §3, §5).
  case "$BUILDER" in
    A) exec codex login --device-auth ;;
    B) echo "builder B has no sign-in: its key is held by the egress, the CLI given a stand-in (SPEC §3b)"; exit 2 ;;
  esac
fi

cred_fields() {
  # The names of the credential file's fields, nested ones dotted — never a value.
  python3 -c '
import json, sys
def names(o, p=""):
    return [n for k, v in o.items() for n in [p + k] + (names(v, p + k + ".") if isinstance(v, dict) else [])]
print(" ".join(names(json.load(open(sys.argv[1])))))' "$1"
}

# The time limit runs from the launch print's first second; the print's own time is counted in it (SPEC §6).
case "$TIME_LIMIT" in
  ''|*[!0-9hms]*|[hms]*|*[hms]*[hms]*) echo "TIME_LIMIT: a whole number, then h, m or s: $TIME_LIMIT"; exit 2 ;;
  *h) LIMIT_S=$(( 10#${TIME_LIMIT%h} * 3600 )) ;;
  *m) LIMIT_S=$(( 10#${TIME_LIMIT%m} * 60 )) ;;
  *s) LIMIT_S=$(( 10#${TIME_LIMIT%s} )) ;;
  *) LIMIT_S=$(( 10#$TIME_LIMIT )) ;;
esac
START=$(date -u +%s); DEADLINE=$(( START + LIMIT_S ))
CAP_LINE="none — its plan's limit"; [ -n "${EGRESS_SPEND_CAP_USD:-}" ] && CAP_LINE="\$${EGRESS_SPEND_CAP_USD} a run, the egress's sum of the generations it lets through"
EXP_LINE=
if [ "$BUILDER" = B ]; then
  # Builder B's experiments file, read as its CLI reads it — an object whose flags and experimentIds, where present,
  # are arrays; the last flag 45773134, DEFAULT_REQUEST_TIMEOUT, its intValue the headers timeout in seconds. A file
  # the CLI cannot read it ignores in silence (SPEC §4.2): the run does not start.
  EXP_LINE=$(python3 -I - "$GEMINI_EXP" <<'PY'
import json, sys
try:
    j = json.load(open(sys.argv[1], encoding="utf-8"))
    f, e = j.get("flags"), j.get("experimentIds")
    assert (f is None or isinstance(f, list)) and (e is None or isinstance(e, list))
    v = [x.get("intValue") for x in f or [] if isinstance(x, dict) and str(x.get("flagId")) == "45773134"]
    s = int(str(v[-1]).strip())
    assert s > 0
    print(f"DEFAULT_REQUEST_TIMEOUT {s} s, the CLI's headers timeout")
except Exception as x:
    print("UNREAD: " + type(x).__name__)
    sys.exit(1)
PY
) || { echo "the experiments file $GEMINI_EXP: $EXP_LINE — the CLI would ignore it in silence: the run does not start"; exit 3; }
fi

{
  echo "=== launch print · run ${RUN_ID} · ${RUN_KIND} · builder ${BUILDER} · $(date -u -d "@$START" +%Y-%m-%dT%H:%M:%SZ)"
  echo "image: ${BUILDER_IMAGE_ID}"
  echo "platform: $(uname -sm)"
  case "$BUILDER" in
    A) echo "cli: $(codex --version 2>&1)" ;;
    B) echo "cli: gemini $(gemini --version 2>&1)" ;;
  esac
  echo "python: $(python3 -c 'import sys, numpy, scipy; print(sys.version.split()[0], "· numpy", numpy.__version__, "· scipy", scipy.__version__)' 2>&1)"
  echo "poppler: $(pdftotext -v 2>&1 | head -1)"
  echo "node: $(node --version)"
  echo "model: ${MODEL} · the egress's route: ${EGRESS_ROUTE} · models allowed at the egress: ${EGRESS_MODELS} · the spend cap at the egress: ${CAP_LINE} · the model that served each request: the egress log · time limit: ${TIME_LIMIT} from this print's first line — deadline $(date -u -d "@$DEADLINE" +%Y-%m-%dT%H:%M:%SZ)"
  echo "--- the configuration: $CONFIG · sha256 $(sha256sum "$CONFIG" | cut -d' ' -f1)"
  cat "$CONFIG"
  echo "--- end of the configuration"
  if [ "$BUILDER" = B ]; then
    echo "--- the experiments file: GEMINI_EXP=$GEMINI_EXP · sha256 $(sha256sum "$GEMINI_EXP" | cut -d' ' -f1)"
    cat "$GEMINI_EXP"
    echo "--- end of the experiments file — read as the CLI reads it: $EXP_LINE"
  fi
  if [ "$BUILDER" = A ]; then
    echo "--- codex features list"
    codex features list 2>&1
    echo "--- end of the features"
  fi
  echo "--- the inputs: sha256 of every file under /in"
  sha256sum /in/brief.md
  find /in -type f ! -path /in/brief.md -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
  echo "--- end of the inputs"
  echo "--- the files mounted read-only beside the inputs: sha256 of every file under /envelope and /ca"
  find /envelope /ca -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
  echo "--- end of the mounted files"
  echo "user: $(id -u):$(id -g) · HOME $HOME · working folder $(pwd)"
  for p in "$HOME/.ssh" "$HOME/.gitconfig" "$HOME/.git-credentials" "$HOME/.config/git" /etc/gitconfig; do
    if [ -e "$p" ]; then echo "present: $p"; else echo "absent: $p"; fi
  done
  echo "git configuration lines, every scope: $(git config --list --show-origin 2>/dev/null | wc -l)"
  echo "environment variable names: $(env | cut -d= -f1 | LC_ALL=C sort | paste -sd' ' -)"
  echo "files under HOME and CODEX_HOME at the start: $(find "$HOME" "$CODEX_HOME" -type f 2>/dev/null | LC_ALL=C sort | paste -sd' ' -)"
  if [ "$BUILDER" = B ]; then
    if [ -n "${GEMINI_API_KEY:-}" ]; then echo "the key: GEMINI_API_KEY set — a stand-in, the real key held by the egress (run.sh's check on the console)"
    else echo "the key: GEMINI_API_KEY ABSENT"; fi
  elif [ -s "$CRED" ]; then echo "credentials: $CRED present · its fields: $(cred_fields "$CRED" 2>&1) · its tokens stand-ins, the real ones held by the egress (run.sh's check on the console)"
  else echo "credentials: $CRED ABSENT"; fi
  echo "=== launch print ends · $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} 2>&1 | tee "$L/launch.txt"

signal_tree() {
  # $1, a signal: to every process below this script — in the container every process but this one, its PID 1.
  # The tree is read from /proc by the shell's builtins alone, so that the scan starts no process of its own.
  local p q line tree=" $$ " grew=1
  while [ "$grew" = 1 ]; do
    grew=0
    for p in /proc/[0-9]*; do
      p=${p#/proc/}
      case "$tree" in *" $p "*) continue ;; esac
      q=
      while IFS= read -r line; do
        case "$line" in PPid:*) q=${line#PPid:}; q=${q//[[:space:]]/}; break ;; esac
      done 2>/dev/null < "/proc/$p/status"
      case "$tree" in *" $q "*) tree="$tree$p "; grew=1 ;; esac
    done
  done
  for p in $tree; do [ "$p" = "$$" ] || kill "-$1" "$p" 2>/dev/null; done
}

freeze_return() {
  # The return as it stood at the deadline: copied into /logs and hashed, before any grace (SPEC §6).
  cp -a /work/return "$L/return-at-deadline"
  ( cd "$L/return-at-deadline" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum ) > "$L/return-at-deadline.sha256"
  echo "the return at the deadline: logs/return-at-deadline · files $(wc -l < "$L/return-at-deadline.sha256") · its list logs/return-at-deadline.sha256 · sha256 $(sha256sum "$L/return-at-deadline.sha256" | cut -d' ' -f1)"
}

cd /work || exit 3
stopped=no; frozen=; raw=
if [ "$(date -u +%s)" -ge "$DEADLINE" ]; then
  stopped=yes; frozen=$(freeze_return); echo "$frozen"    # the limit ran out during the print: the CLI does not start
else
  case "$BUILDER" in
    A) codex exec --json --skip-git-repo-check --cd /work --output-last-message "$L/last-message.txt" - \
         < /in/brief.md > "$L/cli-events.jsonl" 2> "$L/cli-stderr.txt" & ;;
    B) gemini --model "$MODEL" --approval-mode yolo --output-format stream-json --include-directories /in \
         --prompt "$(cat /in/brief.md)" < /dev/null > "$L/cli-events.jsonl" 2> "$L/cli-stderr.txt" & ;;
  esac
  cli=$!
  while kill -0 "$cli" 2>/dev/null && [ "$(date -u +%s)" -lt "$DEADLINE" ]; do sleep 1; done
  if kill -0 "$cli" 2>/dev/null; then
    # The deadline with the CLI running: every process below this script stopped, the return copied and hashed,
    # then TERM, a grace of 60 seconds for the CLI, then KILL.
    stopped=yes
    signal_tree STOP; signal_tree STOP
    frozen=$(freeze_return); echo "$frozen"
    signal_tree TERM; signal_tree CONT
    for i in $(seq 60); do kill -0 "$cli" 2>/dev/null || break; sleep 1; done
    signal_tree KILL; signal_tree KILL
  fi
  wait "$cli"; raw=$?
fi
if [ "$stopped" = yes ]; then rc=124; note=" — stopped by the time limit (the status the CLI ended with: ${raw:-none, it did not start})"; else rc=$raw; note=; fi
{ echo "exit status: $rc$note"
  [ "$stopped" = yes ] && echo "$frozen"
  echo "deadline: $(date -u -d "@$DEADLINE" +%Y-%m-%dT%H:%M:%SZ) · ended: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; } | tee "$L/exit.txt"
exit 0
