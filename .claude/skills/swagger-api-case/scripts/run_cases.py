#!/usr/bin/env python3
"""
run_cases.py -- Python case runner for environments without the Windows-only run-cases.py
(rule-modules-web-master/.claude/skills/api-case-generate/api-case-run/scripts/run-cases.py).

Reproduces the same cases.json -> report.json contract used by that tool:
  - config.json: variables / base_urls / auth (login) / headers
  - cases.json: list of cases, each with steps (method/base_url/path/request_body/extract_vars/expected_response)
  - {{var}} substitution from config.variables + extract_vars accumulated within a case
  - extract_vars path syntax: dotted keys with [n] array indices, e.g. "data.list[0].id"
  - expected_response assertion operators: $not_empty / $is_array / $gte / $length_gte, plain equality otherwise
  - report.json: {config, started_at, finished_at, total, passed, failed, skipped, cases:[{name,status,pass,steps:[...]}]}

Usage:
  python3 run_cases.py --cases path/to/cases.json --config path/to/config.json --out path/to/report.json
"""
import argparse
import copy
import json
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_path(obj, path):
    """dotted path with [n] array index support (e.g. data.list[0].id) AND
    [field=value] array filter support (e.g. data[templateName=foo].id), which
    finds the first array element whose field equals value (compared as str)."""
    tokens = re.findall(r"[^.\[\]]+|\[[^\]]*\]", path)
    cur = obj
    for tok in tokens:
        if tok.startswith("["):
            inner = tok[1:-1]
            if inner.isdigit():
                idx = int(inner)
                if not isinstance(cur, list) or idx >= len(cur):
                    return None
                cur = cur[idx]
            elif "=" in inner:
                key, _, value = inner.partition("=")
                if not isinstance(cur, list):
                    return None
                match = None
                for item in cur:
                    if isinstance(item, dict) and str(item.get(key)) == value:
                        match = item
                        break
                if match is None:
                    return None
                cur = match
            else:
                return None
        else:
            if not isinstance(cur, dict) or tok not in cur:
                return None
            cur = cur[tok]
    return cur


# Supports dotted, namespaced references like {{variables.platform}} and
# {{base_urls.RULEBASEURL}}, as well as flat names {{token}} / extracted vars.
VAR_RE = re.compile(r"\{\{([\w.]+)\}\}")

_MISSING = object()


def resolve_var(key, context):
    """Resolve a (possibly dotted) variable key against the context dict.

    Lookup order:
      1. dotted path navigation, e.g. "variables.platform" -> context["variables"]["platform"]
      2. backward-compat fallback for a flat name: search the "variables" and
         "base_urls" namespaces so old-style {{platform}} / {{BASEURL}} still resolve.
    Returns _MISSING when the key cannot be resolved.
    """
    cur = context
    ok = True
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            ok = False
            break
    if ok:
        return cur
    if "." not in key:
        for ns in ("variables", "base_urls"):
            d = context.get(ns)
            if isinstance(d, dict) and key in d:
                return d[key]
    return _MISSING


def substitute(obj, context):
    if isinstance(obj, str):
        m = VAR_RE.fullmatch(obj)
        if m:
            val = resolve_var(m.group(1), context)
            if val is not _MISSING:
                return val

        def repl(match):
            val = resolve_var(match.group(1), context)
            return match.group(0) if val is _MISSING else str(val)

        return VAR_RE.sub(repl, obj)
    if isinstance(obj, dict):
        return {k: substitute(v, context) for k, v in obj.items()}
    if isinstance(obj, list):
        return [substitute(v, context) for v in obj]
    return obj


def build_context(config, token, extra=None):
    """Namespaced substitution context.

    - {{variables.X}}  -> config.variables.X
    - {{base_urls.X}}  -> config.base_urls.X
    - {{token}}        -> fresh login token (top-level, NOT config.variables.token)
    - {{extracted}}    -> values pulled from earlier step responses (top-level)
    Flat legacy names still resolve via resolve_var's fallback.
    """
    ctx = {
        "variables": dict(config.get("variables", {})),
        "base_urls": dict(config.get("base_urls", {})),
        "token": token,
    }
    if extra:
        ctx.update(extra)
    return ctx


def http_request(method, url, headers, body):
    data = None
    if method.upper() != "GET" or body:
        data = json.dumps(body if body is not None else {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=260) as resp:
            raw = resp.read()
            return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def login(config):
    auth = config["auth"]
    headers = {"Content-Type": "application/json"}
    headers.update(auth.get("headers", {}))
    status, raw = http_request(auth.get("method", "POST"), auth["login_url"], headers, auth.get("body", {}))
    body = json.loads(raw.decode("utf-8"))
    token = get_path(body, auth["token_path"])
    if not token:
        raise RuntimeError(f"Login failed, status={status}, body={body}")
    return auth.get("token_prefix", "") + token


def data_shape_of(data):
    if isinstance(data, list):
        return "list"
    if isinstance(data, dict):
        return "dict"
    if data is None:
        return "null"
    return type(data).__name__


def check_assertion(expected, actual, path_prefix, failures):
    if isinstance(expected, dict) and len(expected) == 1 and next(iter(expected)) in (
        "$not_empty", "$is_array", "$gte", "$length_gte",
    ):
        op = next(iter(expected))
        val = expected[op]
        if op == "$not_empty":
            ok = actual not in (None, {}, [], "")
            if val is False:
                ok = not ok
        elif op == "$is_array":
            ok = isinstance(actual, list) if val else True
        elif op == "$gte":
            ok = actual is not None and actual >= val
        elif op == "$length_gte":
            ok = actual is not None and len(actual) >= val
        else:
            ok = False
        if not ok:
            failures.append(f"{path_prefix}: expected {op}={val}, got {actual!r}")
        return
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            failures.append(f"{path_prefix}: expected dict, got {actual!r}")
            return
        for k, v in expected.items():
            check_assertion(v, actual.get(k), f"{path_prefix}.{k}", failures)
        return
    if actual != expected:
        failures.append(f"{path_prefix}: expected {expected!r}, got {actual!r}")


def run_case(case, config, base_context, base_headers):
    case_ctx = dict(base_context)
    step_reports = []
    case_pass = True
    for step in case["steps"]:
        method = step["method"]
        base_url_raw = step.get("base_url", "")
        base_url = substitute(base_url_raw, case_ctx)
        path = substitute(step.get("path", ""), case_ctx)
        if path:
            url = base_url.rstrip("/") + path if path.startswith("/") else base_url.rstrip("/") + "/" + path
        else:
            url = base_url
        request_body = substitute(step.get("request_body", {}), case_ctx)

        def build_headers():
            # step-level headers override config default; {{headers}} resolves to
            # the config's resolved headers object. Falls back to base_headers.
            if "headers" in step:
                resolved = substitute(step["headers"], case_ctx)
                return dict(resolved) if isinstance(resolved, dict) else dict(base_headers)
            return dict(base_headers)

        t0 = time.time()
        try:
            headers = build_headers()
            status_code, raw = http_request(method, url, headers, request_body)
            if status_code == 401:
                # token expired mid-run: re-login, refresh the shared token so
                # this and all later cases use it, then retry once.
                new_token = login(config)
                base_context["token"] = new_token
                case_ctx["token"] = new_token
                if isinstance(base_headers, dict) and "Authorization" in base_headers:
                    base_headers["Authorization"] = new_token  # in place -> {{headers}} sees it
                headers = build_headers()
                status_code, raw = http_request(method, url, headers, request_body)
        except Exception as e:
            step_reports.append({
                "name": step.get("name", ""), "method": method, "url": url,
                "status_code": None, "ms": int((time.time() - t0) * 1000),
                "pass": False, "failures": [f"request error: {e}"],
                "resp_code": None, "resp_keys": [], "data_shape": None, "data_len": None, "msg": None,
            })
            case_pass = False
            continue
        ms = int((time.time() - t0) * 1000)
        is_json = True
        try:
            resp_json = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            resp_json = {}
            is_json = False

        expected = step.get("expected_response", {})
        failures = []
        if isinstance(expected, dict) and "$binary" in expected:
            # Non-JSON binary response (e.g. xlsx/csv export download): check raw byte size
            # instead of JSON assertions, since json.loads() cannot parse binary payloads.
            spec = expected["$binary"] or {}
            min_size = spec.get("$min_size", 1)
            raw_len = len(raw) if raw else 0
            if raw_len < min_size:
                failures.append(f"resp.$binary: expected size >= {min_size}, got {raw_len}")
        else:
            check_assertion(expected, resp_json, "resp", failures)

        # propagate extracted vars for later steps in this case (top-level / flat)
        for var_name, extract_path in step.get("extract_vars", {}).items():
            val = get_path(resp_json, extract_path)
            if val is not None:
                case_ctx[var_name] = val

        data = resp_json.get("data") if isinstance(resp_json, dict) else None
        step_pass = status_code == 200 and not failures
        if not step_pass:
            case_pass = False
        step_reports.append({
            "name": step.get("name", ""), "method": method, "url": url,
            "status_code": status_code, "ms": ms,
            "pass": step_pass, "failures": failures,
            "resp_code": resp_json.get("code") if isinstance(resp_json, dict) else None,
            "resp_keys": list(resp_json.keys()) if isinstance(resp_json, dict) else [],
            "data_shape": data_shape_of(data),
            "data_len": len(data) if isinstance(data, (list, dict)) else None,
            "msg": resp_json.get("msg") if isinstance(resp_json, dict) else None,
        })
    return {
        "name": case["name"], "status": "passed" if case_pass else "failed",
        "pass": case_pass, "steps": step_reports,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)
    with open(args.cases, "r", encoding="utf-8") as f:
        cases = json.load(f)

    token = login(config)
    base_context = build_context(config, token)
    base_headers = substitute(config.get("headers", {}), base_context)
    # expose the resolved config headers so cases can reference them via {{headers}}
    base_context["headers"] = base_headers

    started_at = now_iso()
    case_reports = []
    passed = failed = skipped = 0
    for case in cases:
        if case.get("skip"):
            case_reports.append({
                "name": case["name"], "status": "skipped", "pass": None,
                "steps": [], "skip_reason": case.get("skip_reason", ""),
            })
            skipped += 1
            continue
        report = run_case(case, config, base_context, base_headers)
        case_reports.append(report)
        if report["pass"]:
            passed += 1
        else:
            failed += 1
    finished_at = now_iso()

    report = {
        "config": config.get("name", ""),
        "started_at": started_at,
        "finished_at": finished_at,
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "cases": case_reports,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"total={len(cases)} passed={passed} failed={failed}")


if __name__ == "__main__":
    main()
