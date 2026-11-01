# The envelope's egress — a mitmproxy addon (replicability test 01, the envelope's spec, §3).
#
# Each builder reaches its model by its own route: EGRESS_ROUTE `chatgpt` (builder A, its plan's sign-in),
# `gemini-api` (builder B, the Gemini API with a key) or `google` (the Code Assist route, kept with its
# controls, not run), in EGRESS_PHASE `signin` (the operator's sign-in, once per run) or `run` (the
# builder's run); `gemini-api` has no sign-in. The egress:
#   - allows its route's hosts, port 443, and on them its route's paths for this phase alone; every
#     other connection or request is refused (403) and logged;
#   - holds the plan's credentials: each token a token endpoint answers is kept in EGRESS_VAULT and
#     the CLI is given a stand-in — a JWT keeps its header and its claims, its personal claims masked
#     and its signature replaced; any other token is replaced whole. On each request the real token
#     is put where its stand-in stands — the Authorization header, a token request's body, a query's
#     access_token; a request carrying a token the egress does not hold, or an API key, is refused;
#   - on `gemini-api`, holds the key: run.sh writes it with its stand-in into EGRESS_VAULT before the
#     egress starts, and the builder holds the stand-in alone; on each request the egress puts the key
#     where its stand-in stands — the x-goog-api-key header, a query's key, a bearer token; another key,
#     another key header, or a request carrying none, is refused; without its one key it does not start;
#   - on `gemini-api`, counts the spend as the vendor may bill it: every generation it lets through, priced
#     at RATES for the date it ends, summed for the run and logged on a `use` line — one answered whole by
#     the usageMetadata its answer carries, a stream's last event's or a JSON answer's; one cut after its
#     answer's headers, or before any answer, at a bound: BOUND thinking and output tokens, its input by
#     the last use its events carried, else uncached by its body's bytes at the run's last ratio, re-priced
#     by its resend's own use when the CLI sends the same body again; a stream's events and those carrying
#     a use counted on its line; once the sum reaches EGRESS_SPEND_CAP_USD, every further generation is
#     refused with 402, its reason logged; an answer that ends whole without a use it can read, or a
#     generation it cannot price, stops the count the same way; without its cap or its model's rates it
#     does not start;
#   - ends TLS under this run's own CA and reads each request: its model, its reasoning or thinking
#     setting, every tool it declares, a namespace's tools at any depth; a request naming a model
#     outside EGRESS_MODELS, declaring a tool its vendor runs to reach beyond its servers, or carrying
#     a namespace whose tools it cannot read, is refused (403); a WebSocket upgrade, 426;
#   - on `chatgpt`, reads builder A's generation streams as they pass, unchanged, for the model that
#     served — each answer to a generation asked with `stream` true and answered 200, tapped by its
#     request whatever its content-type, the route's answers carrying none —: on a `served` line at
#     each stream's end or cut, the model each response.created,
#     response.completed or response.incomplete event names, any openai-model or x-openai-model in an
#     event's response.headers or headers, the safety_buffering value its CLI reads by its kind alone —
#     absent, false, an object or a response.metadata of that type with its retry_model, any other by its
#     type — nothing else;
#   - logs each connection, request and response as one JSON line in $EGRESS_LOG_DIR/egress.jsonl,
#     flushed line by line — never a header, a token or a stand-in; keeps the bodies of the model's
#     requests, gzip-compressed, under bodies/, and the plan's own answers on its use and limits;
#   - fails closed: an error inside any of its hooks refuses the request, or replaces the response.
# At load it writes $EGRESS_LOG_DIR/addon-ready-<phase>.json, which the egress's health check needs:
# a script mitmproxy could not load leaves the builder unstarted.
import base64
import gzip
import hashlib
import json
import os
import re
import secrets
import threading
import zlib
from datetime import datetime, timezone
from decimal import ROUND_CEILING, Decimal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from mitmproxy import http

ROUTE = os.environ.get("EGRESS_ROUTE", "")
PHASE = os.environ.get("EGRESS_PHASE", "")
if ROUTE not in ("chatgpt", "google", "gemini-api") or PHASE not in ("signin", "run"):
    raise ValueError("EGRESS_ROUTE must be chatgpt, google or gemini-api, EGRESS_PHASE signin or run")
if ROUTE == "gemini-api" and PHASE != "run":
    raise ValueError("the gemini-api route has no sign-in: EGRESS_PHASE must be run")
MODELS = {m.strip() for m in os.environ.get("EGRESS_MODELS", "").split(",") if m.strip()}
if PHASE == "run" and not MODELS:
    raise ValueError("EGRESS_MODELS must name the run's model")
LOG_DIR = os.environ.get("EGRESS_LOG_DIR", "/egress")
VAULT_DIR = os.environ.get("EGRESS_VAULT", "/vault")
VAULT_FILE = os.path.join(VAULT_DIR, "vault.json")
# Builder B's spend cap — the gemini-api route alone —, US dollars a run, and its vendor's rates per 1M tokens: input
# not cached, input cached, output with its thinking; the newest first, each from its date (UTC) on.
RATES = {
    "gemini-4-argon": (("2026-12-01T00:00:00+00:00", "4.00", "0.20", "20.00"),
                       ("2026-01-01T00:00:00+00:00", "2.00", "0.10", "10.00")),
}
CAP = None
if ROUTE == "gemini-api":
    try:
        CAP = Decimal(os.environ.get("EGRESS_SPEND_CAP_USD", "").strip())
    except Exception:
        CAP = None
    if CAP is None or not CAP.is_finite() or CAP <= 0:
        raise ValueError("the gemini-api route needs its spend cap: EGRESS_SPEND_CAP_USD, a positive number of US dollars")
    if any(m not in RATES for m in MODELS):
        raise ValueError("the gemini-api route prices each answer: no rates for "
                         + ", ".join(sorted(m for m in MODELS if m not in RATES)))
GENERATION = re.compile(r":(streamGenerateContent|generateContent)$")
# A generation let through whose use the egress does not read whole — cut, by the client or the server, after its
# answer's headers or before any answer — is counted at a bound: BOUND thinking and output tokens at the output rate, or
# what its events showed where more; its input by the last use its events carried, else uncached by its request body's
# bytes at the run's last ratio of a body's bytes to its prompt's tokens — one byte a token before any answer set it.
BOUND = 32768
LIMIT_TERMS = ("prepay", "credit", "balance", "depleted", "billing", "spending cap", "spend cap", "spending limit",
               "quota")

S, R = {"signin"}, {"run"}
B = S | R
# (methods, host, path — matched whole, without its query —, phases, kind)
ROUTES = {
    "chatgpt": [
        ({"POST"}, "auth.openai.com", r"/api/accounts/deviceauth/usercode", S, "signin"),
        ({"POST"}, "auth.openai.com", r"/api/accounts/deviceauth/token", S, "signin"),
        ({"POST"}, "auth.openai.com", r"/oauth/token", B, "token"),
        ({"POST"}, "auth.openai.com", r"/oauth/revoke", S, "token"),
        ({"POST"}, "chatgpt.com", r"/backend-api/codex/responses", R, "generate"),
        ({"GET"}, "chatgpt.com", r"/backend-api/codex/models", R, "models"),
        ({"GET"}, "chatgpt.com", r"/backend-api/wham/accounts/check", R, "account"),
    ],
    "google": [
        ({"POST"}, "oauth2.googleapis.com", r"/token", B, "token"),
        ({"POST"}, "oauth2.googleapis.com", r"/tokeninfo", B, "tokeninfo"),
        ({"GET"}, "www.googleapis.com", r"/oauth2/v2/userinfo", S, "userinfo"),
        ({"POST"}, "cloudcode-pa.googleapis.com",
         r"/v1internal:(loadCodeAssist|onboardUser|retrieveUserQuota|listExperiments|fetchAdminControls)", B, "setup"),
        ({"GET"}, "cloudcode-pa.googleapis.com", r"/v1internal/operations/[A-Za-z0-9_.~-]+", B, "setup"),
        ({"GET", "POST"}, "cloudcode-pa.googleapis.com",
         r"/v1internal:(getCodeAssistGlobalUserSetting|setCodeAssistGlobalUserSetting)", S, "setup"),
        ({"POST"}, "cloudcode-pa.googleapis.com", r"/v1internal:(streamGenerateContent|generateContent|countTokens)", R,
         "generate"),
        ({"POST"}, "cloudcode-pa.googleapis.com", r"/v1internal:recordCodeAssistMetrics", R, "metrics"),
    ],
    "gemini-api": [
        ({"POST"}, "generativelanguage.googleapis.com",
         r"/v1(alpha|beta)?/models/[A-Za-z0-9._-]+:(streamGenerateContent|generateContent|countTokens)", R, "generate"),
        ({"GET"}, "generativelanguage.googleapis.com", r"/v1(alpha|beta)?/models(/[A-Za-z0-9._-]+)?", R, "models"),
    ],
}[ROUTE]
PATH_MODEL = re.compile(r"/models/([A-Za-z0-9._-]+):")
HOSTS = {r[1] for r in ROUTES}
KEEP_REQUEST = {"generate", "models", "account", "setup", "metrics"}   # never a token request's body
KEEP_RESPONSE = {"setup", "models", "account"}                          # the plan's own answers
TOKEN_FIELDS = {"refresh_token", "access_token", "id_token", "subject_token", "token"}
ISSUED_FIELDS = ("access_token", "refresh_token", "id_token")
PERSONAL = {"email", "name", "given_name", "family_name", "picture", "preferred_username"}
API_KEY_HEADERS = {"x-goog-api-key", "api-key", "x-api-key"}
API_KEY_PARAMS = {"key", "api_key", "apikey"}
DENY_OPENAI = {"mcp", "code_interpreter", "computer_use_preview", "computer", "image_generation", "file_search"}
DENY_GEMINI = {"googleSearch", "googleSearchRetrieval", "urlContext", "codeExecution", "googleMaps",
               "enterpriseWebSearch", "computerUse", "retrieval", "fileSearch"}
CLIENT_TOOL_TYPES = {"function", "custom", "local_shell"}
NAMESPACE_DEPTH = 4   # a namespace nested deeper is one whose tools the egress cannot read
SERVED_EVENTS = ("response.created", "response.completed", "response.incomplete")
SERVED_HEADERS = ("openai-model", "x-openai-model")
NOT_LOGGED = {"x-codex-turn-state"}   # an opaque routing value the CLI replays within a turn — not a number or a flag

_lock = threading.Lock()
_seq = [0]
_spend = {"usd": Decimal(0), "answers": 0, "unread": 0, "bound": 0}
_ratio = [None]   # the run's last ratio of a generation's body bytes to its prompt's tokens, set by each answered use
_pending = {}     # a body's sha256 -> its sends counted by their bytes, each re-priced by a resend's own use
os.makedirs(os.path.join(LOG_DIR, "bodies"), exist_ok=True)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _log(rec):
    line = json.dumps({"t": _now(), "phase": PHASE, **rec}, ensure_ascii=False)
    with _lock:
        with open(os.path.join(LOG_DIR, "egress.jsonl"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())


def _next():
    with _lock:
        _seq[0] += 1
        return _seq[0]


# --- the vault: real tokens by their stand-ins, kept by the egress alone ---------------------------
def _vault_load():
    try:
        with open(VAULT_FILE, encoding="utf-8") as f:
            v = json.load(f)
    except FileNotFoundError:
        v = {}
    v.setdefault("real_by_standin", {})
    v.setdefault("standin_by_sha", {})
    v.setdefault("issued", {})
    v.setdefault("swapped", {})
    return v


def _vault_save():
    os.makedirs(VAULT_DIR, mode=0o700, exist_ok=True)
    tmp = VAULT_FILE + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(VAULT, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, VAULT_FILE)


VAULT = _vault_load()
if ROUTE == "gemini-api" and len(VAULT["real_by_standin"]) != 1:
    raise ValueError("the gemini-api route needs its one key in the vault, written by run.sh")


def _count(table, key):
    VAULT[table][key] = VAULT[table].get(key, 0) + 1


def _b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _b64e(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _mask(o):
    if isinstance(o, dict):
        return {k: (("withheld@egress.invalid" if k == "email" else "withheld-by-egress")
                    if k in PERSONAL and isinstance(v, str) else _mask(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [_mask(x) for x in o]
    return o


def _jwt_standin(tok):
    parts = tok.split(".")
    if len(parts) != 3:
        return None
    try:
        header = json.loads(_b64d(parts[0]))
        claims = json.loads(_b64d(parts[1]))
    except Exception:
        return None
    if not isinstance(header, dict) or "alg" not in header or not isinstance(claims, dict):
        return None
    body = json.dumps(_mask(claims), ensure_ascii=False, separators=(",", ":")).encode()
    return parts[0] + "." + _b64e(body) + "." + _b64e(secrets.token_bytes(32))


def _issue(real, field):
    """The stand-in for a real token — the same one each time the same token is answered."""
    sha = hashlib.sha256(real.encode()).hexdigest()
    with _lock:
        known = VAULT["standin_by_sha"].get(sha)
        if known:
            return known
        standin = _jwt_standin(real) or f"rt01.{field}.{secrets.token_urlsafe(32)}"
        VAULT["real_by_standin"][standin] = real
        VAULT["standin_by_sha"][sha] = standin
        _count("issued", field)
        _vault_save()
        return standin


def _real(standin, where):
    with _lock:
        real = VAULT["real_by_standin"].get(standin)
        if real is not None:
            _count("swapped", where)
            _vault_save()
        return real


# --- reading a request ----------------------------------------------------------------------------
def _route(method, host, path):
    """(kind, phases) of the route entry the request matches, or None."""
    for methods, h, pattern, phases, kind in ROUTES:
        if h == host and method in methods and re.fullmatch(pattern, path):
            return kind, phases
    return None


def _shown_path(p):
    u = urlsplit(p)
    q = [(k, "REDACTED" if k.lower() in TOKEN_FIELDS | API_KEY_PARAMS else v)
         for k, v in parse_qsl(u.query, keep_blank_values=True)]
    return urlunsplit(("", "", u.path, urlencode(q), ""))


def _denied(kind):
    return "web_search" in kind or kind in DENY_OPENAI or kind in DENY_GEMINI


def _tools(decls, prefix="", depth=0):
    """The tools a request declares: a client tool by its name, any other by its kind; a namespace's tools read at any
    depth, each name under its namespace's; a namespace without a list of tools, or nested deeper than NAMESPACE_DEPTH,
    kept as the kind `namespace`, which the egress refuses."""
    names, kinds = [], []
    for t in decls or []:
        if not isinstance(t, dict):
            continue
        if "functionDeclarations" in t:
            names += [d.get("name") for d in t.get("functionDeclarations") or [] if isinstance(d, dict)]
            kinds += [k for k in t if k != "functionDeclarations"]
        elif "type" not in t:
            kinds += sorted(t.keys())
        elif t["type"] == "namespace":
            if isinstance(t.get("tools"), list) and depth < NAMESPACE_DEPTH:
                n, k = _tools(t["tools"], prefix + str(t.get("name") or "") + ".", depth + 1)
                names += n
                kinds += k
            else:
                kinds.append("namespace")
        elif t["type"] in CLIENT_TOOL_TYPES:
            name = t.get("name") or (t.get("function") or {}).get("name") or t["type"]
            names.append(prefix + str(name) if prefix else name)
        else:
            kinds.append(str(t["type"]))
    return names, kinds


def _summary(body, path_model=None):
    """The model, the setting and the tools a generation request carries — every route's shapes; on the
    Gemini API the model is its path's, and a model its body names besides is read too."""
    s = {}
    try:
        j = json.loads(body)
    except Exception:
        return None
    if not isinstance(j, dict):
        return None
    inner = j.get("request") if isinstance(j.get("request"), dict) else (
        j.get("generateContentRequest") if isinstance(j.get("generateContentRequest"), dict) else {})
    model = path_model or j.get("model") or inner.get("model")
    if isinstance(model, str):
        s["model"] = model[len("models/"):] if model.startswith("models/") else model
    other = (j.get("model") or inner.get("model")) if path_model else None
    if isinstance(other, str):
        other = other[len("models/"):] if other.startswith("models/") else other
        if other != s.get("model"):
            s["body_model"] = other
    for k in ("reasoning", "store", "stream", "parallel_tool_calls"):
        if k in j:
            s[k] = j[k]
    for gc in (j.get("generationConfig"), inner.get("generationConfig")):
        if isinstance(gc, dict) and "thinkingConfig" in gc:
            s["thinking"] = gc["thinkingConfig"]
    decls = list(j.get("tools") or []) + list(inner.get("tools") or [])
    for item in j.get("input") or []:
        if isinstance(item, dict) and item.get("type") == "additional_tools":
            decls += list(item.get("tools") or [])
    names, kinds = _tools(decls)
    if names or kinds:
        s["tools"] = names
        s["server_side_tools"] = kinds
    return s


def _form(body):
    return parse_qsl(body.decode("utf-8"), keep_blank_values=True)


def _swap_body(body, ctype):
    """A token request's body with each stand-in replaced: (new body, fields swapped) or a refusal."""
    if not body:
        return body, []
    if "json" in ctype:
        j = json.loads(body)
        if not isinstance(j, dict):
            return body, []
        swapped = []
        for k in [k for k in j if k in TOKEN_FIELDS]:
            real = _real(j[k], "body") if isinstance(j[k], str) else None
            if real is None:
                raise PermissionError(f"a token the egress does not hold: {k}")
            j[k] = real
            swapped.append(k)
        return (json.dumps(j).encode() if swapped else body), swapped
    pairs = _form(body)
    swapped, out = [], []
    for k, v in pairs:
        if k in TOKEN_FIELDS:
            real = _real(v, "body")
            if real is None:
                raise PermissionError(f"a token the egress does not hold: {k}")
            v = real
            swapped.append(k)
        out.append((k, v))
    return (urlencode(out).encode() if swapped else body), swapped


def _refuse(flow, why, status=403):
    flow.response = http.Response.make(status, f"refused by the envelope's egress: {why}\n".encode(),
                                       {"content-type": "text/plain"})


def _judge(kind, s):
    if kind != "generate":
        return None
    if s is None:
        return "a body the egress cannot read"
    if "model" not in s:
        return "a generation request naming no model"
    if "namespace" in s.get("server_side_tools", []):
        return "a tool namespace the egress cannot read"
    denied = [k for k in s.get("server_side_tools", []) if _denied(k)]
    if denied:
        return "a server-side tool: " + ", ".join(denied)
    if s["model"] not in MODELS:
        return "a model outside the envelope's: " + s["model"]
    if "body_model" in s and s["body_model"] not in MODELS:
        return "a model outside the envelope's: " + s["body_model"]
    return None


def _swap_key(req, url, swaps):
    """The gemini-api route: the key put where its stand-in stands; None, or why the request is refused."""
    found = 0
    for h in sorted(API_KEY_HEADERS):
        if h in req.headers:
            if h != "x-goog-api-key":
                return "an API key header the route does not use: " + h
            real = _real(req.headers[h].strip(), "header")
            if real is None:
                return "a key the egress does not hold"
            req.headers[h] = real
            swaps.append(h)
            found += 1
    q = parse_qsl(url.query, keep_blank_values=True)
    if any(k.lower() in API_KEY_PARAMS for k, _ in q):
        out = []
        for k, v in q:
            if k.lower() in API_KEY_PARAMS:
                real = _real(v, "query")
                if real is None:
                    return "a key the egress does not hold"
                v = real
                swaps.append("query:" + k)
                found += 1
            out.append((k, v))
        req.path = urlunsplit(("", "", url.path, urlencode(out), ""))
    auth = req.headers.get("authorization")
    if auth is not None:
        parts = auth.split(" ", 1)
        real = _real(parts[1].strip(), "header") if len(parts) == 2 and parts[0].lower() == "bearer" else None
        if real is None:
            return "a credential the egress does not hold"
        req.headers["authorization"] = "Bearer " + real
        swaps.append("authorization")
        found += 1
    if not found:
        return "no key: the route's requests carry the stand-in"
    return None


def _keep(seq, kind, body):
    name = f"{seq:06d}-{kind}.gz"
    with gzip.open(os.path.join(LOG_DIR, "bodies", name), "wb") as f:
        f.write(body)
    return name


# --- builder B's spend: each answered generation's use, priced and summed --------------------------
def _rates(model, when):
    for since, inp, cached, out in RATES[model]:
        if when >= datetime.fromisoformat(since):
            return since, Decimal(inp), Decimal(cached), Decimal(out)
    raise ValueError("no rates for " + when.isoformat())


def _tokens(usage):
    return {k: int(usage.get(f) or 0) for k, f in (
        ("prompt", "promptTokenCount"), ("cached", "cachedContentTokenCount"), ("tool_prompt", "toolUsePromptTokenCount"),
        ("output", "candidatesTokenCount"), ("thoughts", "thoughtsTokenCount"), ("total", "totalTokenCount"))}


def _price(u, rates, out_tokens=None):
    since, inp, cached, out = rates
    uncached = max(u["prompt"] + u["tool_prompt"] - u["cached"], 0)
    o = u["output"] + u["thoughts"] if out_tokens is None else out_tokens
    return (Decimal(uncached) * inp + Decimal(u["cached"]) * cached + Decimal(o) * out) / Decimal(1000000)


def _sums(rec):
    rec.update({"usd_sum": f"{_spend['usd']:.6f}", "answers_priced": _spend["answers"], "answers_bound": _spend["bound"],
                "answers_unread": _spend["unread"], "cap": str(CAP)})
    return rec


def _use(flow, usage, why=None, streamed=False, tap=None):
    """An answered generation's use: its tokens, its price at the rates of the date it ends, the run's sum; a use the
    egress cannot read stops the count — every later generation refused (402). Its prompt sets the run's ratio of a
    body's bytes to its prompt's tokens, and re-prices each earlier send of the same body counted by its bytes."""
    flow.metadata["rt01_priced"] = True
    rec = {"event": "use", "kind": "answered", "seq": flow.metadata.get("rt01_seq"),
           "model": flow.metadata.get("rt01_model"), "streamed": streamed}
    if tap is not None:
        rec.update({"events": tap.events, "events_with_use": tap.with_use})
    u, rates = None, None
    if why is None and not isinstance(usage, dict):
        why = "no usageMetadata in the answer"
    if why is None:
        try:
            u = _tokens(usage)
            rates = _rates(rec["model"], datetime.now(timezone.utc))
        except Exception as e:
            u, why = None, "a use the egress cannot price: " + type(e).__name__
    out = [rec]
    with _lock:
        if u is None:
            _spend["unread"] += 1
            rec.update({"usage": None, "why": why, "usd": None})
        else:
            usd = _price(u, rates)
            _spend["usd"] += usd
            _spend["answers"] += 1
            rec.update({"usage": u, "rates_from": rates[0], "usd": f"{usd:.6f}"})
        _sums(rec)
        prompt = u["prompt"] + u["tool_prompt"] if u else 0
        nbytes, sha = flow.metadata.get("rt01_bytes"), flow.metadata.get("rt01_sha")
        if prompt > 0 and nbytes:
            _ratio[0] = Decimal(nbytes) / Decimal(prompt)
        for e in (_pending.pop(sha, []) if prompt > 0 and sha else []):
            usd_in = Decimal(prompt) * e["rate_in"] / Decimal(1000000)
            delta = usd_in - e["usd_in"]
            _spend["usd"] += delta
            out.append(_sums({"event": "use", "kind": "re-priced", "seq": e["seq"], "model": e["model"], "bound": True,
                              "by": f"its resend's own use, seq {rec['seq']}", "prompt": prompt, "prompt_was": e["prompt"],
                              "usd_input": f"{usd_in:.6f}", "usd_input_was": f"{e['usd_in']:.6f}",
                              "usd_delta": f"{delta:.6f}"}))
    for r in out:
        _log(r)


def _bound(flow, cause):
    """A generation let through whose use the egress did not read whole — cut after its answer's headers, or before any
    answer: BOUND thinking and output tokens, or what its events showed where more; its input by the last use its events
    carried, else uncached by its body's bytes at the run's last ratio, the send kept to be re-priced by a resend's own
    use; priced at the rates of the date it ends, summed and held to the cap like any answer."""
    flow.metadata["rt01_priced"] = True
    tap = flow.metadata.get("rt01_tap")
    rec = {"event": "use", "kind": "bound", "cause": cause, "seq": flow.metadata.get("rt01_seq"),
           "model": flow.metadata.get("rt01_model"), "streamed": tap is not None, "bound": True}
    if tap is not None:
        rec.update({"events": tap.events, "events_with_use": tap.with_use})
    floor = tap.usage if tap is not None and isinstance(tap.usage, dict) else None
    rates = _rates(rec["model"], datetime.now(timezone.utc))
    nbytes, sha = int(flow.metadata.get("rt01_bytes") or 0), flow.metadata.get("rt01_sha")
    with _lock:
        if floor is not None:
            u = _tokens(floor)
            o = max(BOUND, u["output"] + u["thoughts"])
            rec.update({"input_by": "the last use its events carried", "floor": u})
            u = dict(u, output_and_thoughts=o)
        else:
            r = _ratio[0]
            n = int((Decimal(nbytes) / r).to_integral_value(rounding=ROUND_CEILING)) if r else nbytes
            rec["input_by"] = (f"its body's {nbytes} bytes at the run's last ratio, {r:.4f} bytes a token" if r
                               else f"its body's {nbytes} bytes, one byte a token — no ratio yet")
            u = {"prompt": n, "cached": 0, "tool_prompt": 0, "output": 0, "thoughts": 0, "output_and_thoughts": BOUND}
            o = BOUND
            if sha:
                _pending.setdefault(sha, []).append({"seq": rec["seq"], "model": rec["model"], "prompt": n, "rate_in": rates[1],
                                                     "usd_in": Decimal(n) * rates[1] / Decimal(1000000)})
        usd = _price(u, rates, o)
        _spend["usd"] += usd
        _spend["bound"] += 1
        rec.update({"usage": u, "bound_tokens": BOUND, "rates_from": rates[0], "usd": f"{usd:.6f}"})
        _sums(rec)
    _log(rec)


class _UseTap:
    """A streamed generation passed on chunk by chunk, unchanged; its server-sent events read on the side — counted, with
    those carrying a usageMetadata, the last kept. mitmproxy calls it with each chunk, then with b"" at the stream's end."""

    def __init__(self, encoding):
        enc = (encoding or "identity").strip().lower()
        self.dec = None if enc in ("", "identity") else (
            zlib.decompressobj(47) if enc in ("gzip", "x-gzip", "deflate") else False)
        self.buf, self.usage, self.why, self.events, self.with_use = b"", None, None, 0, 0
        if self.dec is False:
            self.why = "a stream encoded " + enc

    def __call__(self, data):
        if self.why is None:
            try:
                raw = data if self.dec is None else (self.dec.decompress(data) if data else self.dec.flush())
                self.buf += raw
                *lines, self.buf = self.buf.split(b"\n")
                if not data:
                    lines, self.buf = lines + [self.buf], b""
                for line in lines:
                    line = line.rstrip(b"\r")
                    if line.startswith(b"data:"):
                        j = json.loads(line[5:].strip() or b"null")
                        self.events += 1
                        if isinstance(j, dict) and isinstance(j.get("usageMetadata"), dict):
                            self.usage = j["usageMetadata"]
                            self.with_use += 1
            except Exception as e:
                self.why = "a stream the egress cannot read: " + type(e).__name__
        return data


class _ServedTap:
    """Builder A's generation stream passed on chunk by chunk, unchanged; its server-sent events read on the side for the
    model that served, where the CLI reads it: the model each response.created, response.completed or response.incomplete
    event names, any openai-model or x-openai-model in an event's response.headers or headers, the safety_buffering
    value the CLI reads, by its kind alone — an event's own field when present, whatever it holds, else a
    response.metadata event's metadata of that type: absent, false, an object or that metadata with its retry_model,
    any other value by its type; nothing else kept. mitmproxy calls it with each chunk, then with b"" at the stream's end."""

    def __init__(self, encoding):
        enc = (encoding or "identity").strip().lower()
        self.dec = None if enc in ("", "identity") else (
            zlib.decompressobj(47) if enc in ("gzip", "x-gzip", "deflate") else False)
        self.buf, self.why, self.events, self.logged = b"", None, 0, False
        self.named, self.header_models = {}, []
        self.buffering = {"absent": 0, "false": 0, "object": [], "metadata": [], "other": {}}
        if self.dec is False:
            self.why = "a stream encoded " + enc

    def _event(self, j):
        if not isinstance(j, dict):
            return
        kind = j.get("type")
        resp = j.get("response") if isinstance(j.get("response"), dict) else {}
        if kind in SERVED_EVENTS and isinstance(resp.get("model"), str):
            seen = self.named.setdefault(kind, [])
            if resp["model"] not in seen:
                seen.append(resp["model"])
        for h in (resp.get("headers"), j.get("headers")):
            if isinstance(h, dict):
                for k, v in h.items():
                    for m in (v if isinstance(v, list) else [v]):
                        if str(k).lower() in SERVED_HEADERS and isinstance(m, str) and m not in self.header_models:
                            self.header_models.append(m)
        sb, meta, b = j.get("safety_buffering"), j.get("metadata"), self.buffering
        if "safety_buffering" in j:
            if sb is False:
                b["false"] += 1
            elif isinstance(sb, dict):
                rm = sb.get("retry_model")
                b["object"].append({"event": kind if isinstance(kind, str) else None,
                                    "retry_model": rm if isinstance(rm, str) else None})
            else:
                t = "null" if sb is None else "true" if sb is True else type(sb).__name__
                b["other"][t] = b["other"].get(t, 0) + 1
        elif kind == "response.metadata" and isinstance(meta, dict) and meta.get("type") == "safety_buffering":
            rm = meta.get("retry_model")
            b["metadata"].append({"retry_model": rm if isinstance(rm, str) else None})
        else:
            b["absent"] += 1

    def __call__(self, data):
        if self.why is None:
            try:
                raw = data if self.dec is None else (self.dec.decompress(data) if data else self.dec.flush())
                self.buf += raw
                *lines, self.buf = self.buf.split(b"\n")
                if not data:
                    lines, self.buf = lines + [self.buf], b""
                for line in lines:
                    line = line.rstrip(b"\r")
                    if line.startswith(b"data:"):
                        payload = line[5:].strip()
                        if payload == b"[DONE]":
                            continue
                        self.events += 1
                        self._event(json.loads(payload or b"null"))
            except Exception as e:
                self.why = "a stream the egress cannot read: " + type(e).__name__
        return data

    def record(self, seq, end):
        self.logged = True
        rec = {"event": "served", "seq": seq, "end": end, "events": self.events, "models_named": self.named,
               "header_models": self.header_models, "safety_buffering": self.buffering}
        if self.why:
            rec["why"] = self.why
        elif not self.events:
            rec["why"] = "no server-sent event read"
        return rec


def _error_terms(body):
    """What a generation's error answer names — its status, its reasons, the plan's-limit words its error carries —,
    never the message itself, which can name a project."""
    try:
        j = json.loads(body)
        e = (j[0] if isinstance(j, list) and j else j).get("error")
    except Exception:
        return {"error_read": False}
    if not isinstance(e, dict):
        return {"error_read": False}
    out = {"error_read": True}
    if isinstance(e.get("status"), str):
        out["error_status"] = e["status"]
    reasons = [d.get("reason") for d in e.get("details") or [] if isinstance(d, dict) and isinstance(d.get("reason"), str)]
    if reasons:
        out["error_reasons"] = reasons
    text = json.dumps(e, ensure_ascii=False).lower()
    out["error_terms"] = [t for t in LIMIT_TERMS if t in text]
    return out


# --- the hooks ------------------------------------------------------------------------------------
def http_connect(flow: http.HTTPFlow):
    try:
        host, port = flow.request.host.lower(), flow.request.port
        ok = host in HOSTS and port == 443
        _log({"event": "connect", "host": host, "port": port, "verdict": "allowed" if ok else "refused"})
        if not ok:
            _refuse(flow, "host")
    except Exception as e:
        _refuse(flow, "the egress failed: " + type(e).__name__)


def _request(flow):
    req = flow.request
    host, port, method = req.host.lower(), req.port, req.method.upper()
    url = urlsplit(req.path)
    shown = _shown_path(req.path)
    seq = _next()
    flow.metadata["rt01_seq"] = seq
    rec = {"event": "request", "seq": seq, "host": host, "method": method, "path": shown}
    route = _route(method, host, url.path) if port == 443 else None
    why, status, kind = None, 403, None
    if host not in HOSTS or port != 443:
        why = "host"
    elif req.headers.get("upgrade", "").strip().lower() == "websocket":
        why, status = "a WebSocket upgrade — HTTP only", 426
    elif route is None:
        why = "a path outside the route"
    elif PHASE not in route[1]:
        kind = route[0]
        why = "a path outside this phase"
    else:
        kind = route[0]
    if kind:
        rec["kind"] = kind
    body = req.get_content(strict=False) or b""
    rec["bytes"] = len(body)
    s = None
    if why is None and ROUTE != "gemini-api":
        if any(h in req.headers for h in API_KEY_HEADERS) or any(
                k.lower() in API_KEY_PARAMS for k, _ in parse_qsl(url.query, keep_blank_values=True)):
            why = "an API key on a plan's route"
    if why is None and kind == "generate":
        pm = PATH_MODEL.search(url.path) if ROUTE == "gemini-api" else None
        s = _summary(body, pm.group(1) if pm else None)
        why = _judge(kind, s)
        if s:
            rec.update(s)
    gen = ROUTE == "gemini-api" and kind == "generate" and bool(GENERATION.search(url.path))
    if why is None and gen:
        with _lock:
            spent, unread = _spend["usd"], _spend["unread"]
        if unread:
            why, status = (f"the spend unmeasured: {unread} generation(s) the egress could not count — the spend cap "
                           f"{CAP} USD"), 402
        elif spent >= CAP:
            why, status = f"the spend cap: {spent:.6f} of {CAP} USD by the generations counted", 402
        if why:
            rec["spend_cap"] = True
        else:
            req.headers["accept-encoding"] = "identity"
    if why is None and ROUTE == "chatgpt" and kind == "generate":
        req.headers["accept-encoding"] = "identity"
    swaps = []
    if why is None and ROUTE == "gemini-api":
        why = _swap_key(req, url, swaps)
    if why is None and ROUTE != "gemini-api":
        auth = req.headers.get("authorization")
        if auth is not None:
            parts = auth.split(" ", 1)
            real = _real(parts[1].strip(), "header") if len(parts) == 2 and parts[0].lower() == "bearer" else None
            if real is None:
                why = "a credential the egress does not hold"
            else:
                req.headers["authorization"] = "Bearer " + real
                swaps.append("authorization")
    if why is None:
        q = parse_qsl(url.query, keep_blank_values=True)
        if any(k in TOKEN_FIELDS for k, _ in q):
            out = []
            for k, v in q:
                if k in TOKEN_FIELDS:
                    real = _real(v, "query")
                    if real is None:
                        why = f"a token the egress does not hold: {k}"
                        break
                    v = real
                    swaps.append("query:" + k)
                out.append((k, v))
            if why is None:
                req.path = urlunsplit(("", "", url.path, urlencode(out), ""))
    if why is None and kind in ("token", "tokeninfo") and body:
        try:
            new, fields = _swap_body(body, req.headers.get("content-type", ""))
        except PermissionError as e:
            why = str(e)
        else:
            if fields:
                req.set_content(new)
                swaps += ["body:" + f for f in fields]
            grant = None
            try:
                j = json.loads(body)
                grant = j.get("grant_type") if isinstance(j, dict) else None
            except Exception:
                grant = dict(_form(body)).get("grant_type")
            if grant:
                rec["grant_type"] = grant
    if swaps:
        rec["swapped"] = swaps
    rec["verdict"] = "refused" if why else "allowed"
    if why:
        rec["why"] = why
    else:
        rec["sha256"] = hashlib.sha256(body).hexdigest()
        if body and kind in KEEP_REQUEST:
            rec["body"] = _keep(seq, "request", body)
    _log(rec)
    if why:
        _refuse(flow, why, status)
    else:
        flow.metadata["rt01_kind"] = kind
        flow.metadata["rt01_gen"] = gen
        flow.metadata["rt01_model"] = (s or {}).get("model")
        flow.metadata["rt01_stream"] = (s or {}).get("stream") is True
        flow.metadata["rt01_bytes"] = len(body)
        flow.metadata["rt01_sha"] = rec.get("sha256")


def request(flow: http.HTTPFlow):
    try:
        _request(flow)
    except Exception as e:
        _log({"event": "request", "seq": flow.metadata.get("rt01_seq"), "verdict": "refused",
              "why": "the egress failed: " + type(e).__name__})
        _refuse(flow, "the egress failed: " + type(e).__name__)


def _response_record(flow):
    resp = flow.response
    rec = {"event": "response", "seq": flow.metadata.get("rt01_seq"), "host": flow.request.host,
           "kind": flow.metadata.get("rt01_kind"), "status": resp.status_code,
           "content_type": resp.headers.get("content-type", "")}
    for h in SERVED_HEADERS:
        if h in resp.headers:
            rec[h] = resp.headers[h]
    limits = {k.lower(): v for k, v in resp.headers.items()
              if k.lower().startswith("x-codex-") and k.lower() not in NOT_LOGGED}
    if limits:
        rec["limits"] = limits
    return rec


def responseheaders(flow: http.HTTPFlow):
    try:
        if flow.metadata.get("rt01_kind") is None:
            return
        a_stream = (ROUTE == "chatgpt" and flow.metadata.get("rt01_kind") == "generate"
                    and flow.metadata.get("rt01_stream") is True and flow.response.status_code == 200)
        if a_stream or "text/event-stream" in flow.response.headers.get("content-type", ""):
            if flow.metadata.get("rt01_kind") == "generate":
                if flow.metadata.get("rt01_gen"):
                    tap = _UseTap(flow.response.headers.get("content-encoding"))
                    flow.metadata["rt01_tap"] = tap
                    flow.response.stream = tap
                elif ROUTE == "chatgpt":
                    served = _ServedTap(flow.response.headers.get("content-encoding"))
                    flow.metadata["rt01_served"] = served
                    flow.response.stream = served
                else:
                    flow.response.stream = True
                _log({**_response_record(flow), "streamed": True})
            else:
                flow.response = http.Response.make(502, b"the envelope's egress: a stream it does not pass\n",
                                                   {"content-type": "text/plain"})
    except Exception as e:
        flow.response = http.Response.make(502, b"the envelope's egress failed\n", {"content-type": "text/plain"})
        _log({"event": "response", "seq": flow.metadata.get("rt01_seq"), "error": type(e).__name__})


def _response(flow):
    kind = flow.metadata.get("rt01_kind")
    if kind is None:
        return
    if flow.response.stream:
        served = flow.metadata.get("rt01_served")
        if served is not None and not served.logged:
            _log(served.record(flow.metadata.get("rt01_seq"), "ended"))
        tap = flow.metadata.get("rt01_tap")
        if tap is not None and flow.response.status_code == 200 and not flow.metadata.get("rt01_priced"):
            _use(flow, tap.usage, tap.why, streamed=True, tap=tap)
        return
    rec = _response_record(flow)
    body = flow.response.get_content(strict=False) or b""
    if flow.metadata.get("rt01_gen"):
        if flow.response.status_code == 200:
            try:
                j = json.loads(body)
                usage, why = (j.get("usageMetadata") if isinstance(j, dict) else None), None
            except Exception as e:
                usage, why = None, "an answer the egress cannot read: " + type(e).__name__
            _log(rec)
            _use(flow, usage, why)
            return
        rec.update(_error_terms(body))
    if kind == "token" and body:
        j = json.loads(body)
        issued = []
        if isinstance(j, dict):
            for k in ISSUED_FIELDS:
                if isinstance(j.get(k), str) and j[k]:
                    j[k] = _issue(j[k], k)
                    issued.append(k)
            if "expires_in" in j:
                rec["expires_in"] = j["expires_in"]
        if issued:
            flow.response.set_content(json.dumps(j).encode())
            rec["issued"] = issued
    elif kind in ("userinfo", "tokeninfo") and body:
        j = json.loads(body)
        flow.response.set_content(json.dumps(_mask(j)).encode())
        rec["masked"] = True
    elif kind in KEEP_RESPONSE and body:
        rec["body"] = _keep(flow.metadata.get("rt01_seq") or 0, "response", body)
        rec["sha256"] = hashlib.sha256(body).hexdigest()
    _log(rec)


def response(flow: http.HTTPFlow):
    try:
        _response(flow)
    except Exception as e:
        flow.response = http.Response.make(502, b"the envelope's egress failed\n", {"content-type": "text/plain"})
        _log({"event": "response", "seq": flow.metadata.get("rt01_seq"), "error": type(e).__name__})


def websocket_message(flow: http.HTTPFlow):
    _log({"event": "websocket", "seq": flow.metadata.get("rt01_seq"), "verdict": "refused",
          "why": "a WebSocket the egress does not pass"})
    flow.kill()


def error(flow: http.HTTPFlow):
    _log({"event": "error", "seq": flow.metadata.get("rt01_seq"),
          "host": flow.request.host if flow.request else None, "message": str(flow.error)})
    served = flow.metadata.get("rt01_served")
    if served is not None and not served.logged:
        _log(served.record(flow.metadata.get("rt01_seq"), "cut"))
    if not flow.metadata.get("rt01_gen") or flow.metadata.get("rt01_priced"):
        return
    try:
        if flow.response is None:
            _bound(flow, "cut before any answer")
        elif flow.response.status_code == 200:
            _bound(flow, "cut after its answer's headers")
    except Exception as e:
        flow.metadata["rt01_priced"] = True
        with _lock:
            _spend["unread"] += 1
        _log({"event": "use", "kind": "bound", "seq": flow.metadata.get("rt01_seq"), "usage": None, "usd": None,
              "why": "a cut generation the egress cannot price: " + type(e).__name__})


with open(os.path.join(LOG_DIR, f"addon-ready-{PHASE}.json"), "w", encoding="utf-8") as _f:
    json.dump({"t": _now(), "route": ROUTE, "phase": PHASE, "models": sorted(MODELS),
               "addon_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
               "vault_tokens": len(VAULT["real_by_standin"]),
               "spend_cap_usd": None if CAP is None else str(CAP),
               "bound_tokens": None if CAP is None else BOUND,
               "rates_per_1m": None if CAP is None else {m: RATES[m] for m in sorted(MODELS)}}, _f)
