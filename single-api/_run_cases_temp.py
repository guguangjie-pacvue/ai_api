#!/usr/bin/env python3
"""Temporary single-api case runner (run-cases.py missing from repo)."""
import argparse
import json
import re
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def substitute(obj, variables: dict):
    if isinstance(obj, str):
        def repl(m):
            key = m.group(1)
            return str(variables.get(key, m.group(0)))
        return re.sub(r"\{\{(\w+)\}\}", repl, obj)
    if isinstance(obj, list):
        return [substitute(x, variables) for x in obj]
    if isinstance(obj, dict):
        return {k: substitute(v, variables) for k, v in obj.items()}
    return obj


def get_by_path(data, path: str):
    cur = data
    for part in path.replace("]", "").split("."):
        if "[" in part:
            name, idx = part.split("[", 1)
            if name:
                if not isinstance(cur, dict) or name not in cur:
                    raise KeyError(path)
                cur = cur[name]
            if not isinstance(cur, list):
                raise KeyError(path)
            cur = cur[int(idx)]
        else:
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                raise KeyError(path)
    return cur


def match_expected(actual, expected, path=""):
    failures = []
    if isinstance(expected, dict) and any(str(k).startswith("$") for k in expected.keys()):
        for op, val in expected.items():
            if op == "$is_array":
                if bool(val) and not isinstance(actual, list):
                    failures.append(f"{path}: expected array, got {type(actual).__name__}")
            elif op == "$not_empty":
                empty = actual in (None, "", [], {})
                if bool(val) and empty:
                    failures.append(f"{path}: expected not empty")
            elif op == "$length_gte":
                if not hasattr(actual, "__len__") or len(actual) < val:
                    failures.append(f"{path}: length < {val}")
            elif op == "$gte":
                try:
                    if actual is None or float(actual) < float(val):
                        failures.append(f"{path}: {actual!r} < {val}")
                except (TypeError, ValueError):
                    failures.append(f"{path}: {actual!r} not comparable to {val}")
            else:
                failures.append(f"{path}: unsupported op {op}")
        return failures

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected object, got {type(actual).__name__}"]
        for k, v in expected.items():
            p = f"{path}.{k}" if path else k
            if k not in actual:
                failures.append(f"{p}: missing")
            else:
                failures.extend(match_expected(actual[k], v, p))
        return failures

    if actual != expected:
        failures.append(f"{path}: expected {expected!r}, got {actual!r}")
    return failures


def _decode_payload(raw_bytes, content_type=""):
    ctype = (content_type or "").lower()
    if "json" not in ctype and raw_bytes and raw_bytes[:1] not in (b"{", b"["):
        return {"raw": f"binary:{len(raw_bytes)}", "content_type": content_type}
    text = raw_bytes.decode("utf-8", "replace") if raw_bytes else ""
    try:
        return json.loads(text) if text else None
    except json.JSONDecodeError:
        return {"raw": text[:1000], "content_type": content_type}


def http_json(url, method, headers, body=None, timeout=60):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            payload = _decode_payload(raw, resp.headers.get("Content-Type", ""))
            return resp.status, payload
    except urllib.error.HTTPError as e:
        raw = e.read()
        payload = _decode_payload(raw, e.headers.get("Content-Type", ""))
        return e.code, payload


def login(config):
    auth = config.get("auth") or {}
    if not auth:
        return None
    headers = dict(auth.get("headers") or {})
    headers.setdefault("Content-Type", "application/json")
    status, payload = http_json(
        auth["login_url"],
        auth.get("method", "POST"),
        headers,
        auth.get("body"),
    )
    if status != 200:
        raise RuntimeError(f"login failed HTTP {status}: {payload}")
    token = get_by_path(payload, auth.get("token_path", "data.accessToken"))
    prefix = auth.get("token_prefix", "Bearer ")
    return f"{prefix}{token}"


def build_headers(config, variables):
    headers = substitute(deepcopy(config.get("headers") or {}), variables)
    headers.setdefault("Content-Type", "application/json")
    return headers


def resolve_url(step, variables, base_urls):
    base = step.get("base_url", "")
    if isinstance(base, str) and base.startswith("{{") and base.endswith("}}"):
        key = base[2:-2]
        base = base_urls.get(key) or variables.get(key) or ""
    else:
        base = substitute(base, variables)
    path = substitute(step.get("path", ""), variables)
    url = base.rstrip("/") + "/" + path.lstrip("/")
    query_params = step.get("query_params") or {}
    if query_params:
        from urllib.parse import urlencode
        qs = urlencode({k: substitute(v, variables) for k, v in query_params.items()})
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{qs}"
    return url


def preview_response(payload):
    if not isinstance(payload, dict):
        return payload
    out = {}
    for k in ("code", "success", "msg"):
        if k in payload:
            out[k] = payload[k]
    if "data" in payload:
        data = payload["data"]
        if isinstance(data, list):
            out["data_type"] = "array"
            out["data_len"] = len(data)
            out["data_sample"] = data[:3]
        elif isinstance(data, dict):
            out["data_type"] = "object"
            out["data_keys"] = list(data.keys())[:20]
        else:
            out["data"] = data
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    config = load_json(Path(args.config))
    cases = load_json(Path(args.cases))
    variables = dict(config.get("variables") or {})
    base_urls = dict(config.get("base_urls") or {})
    # expose base urls as variables too
    variables.update(base_urls)

    started = datetime.now(timezone.utc)
    # refresh token
    try:
        token = login(config)
        if token:
            variables["token"] = token
            print("login ok, token refreshed")
    except Exception as e:
        print(f"login warning: {e}; using config token")

    report_cases = []
    passed = failed = skipped = 0

    for case in cases:
        case_name = case.get("name", "")
        step_reports = []
        case_pass = True
        for step in case.get("steps") or []:
            headers = build_headers(config, variables)
            url = resolve_url(step, variables, base_urls)
            body = substitute(deepcopy(step.get("request_body")), variables)
            method = step.get("method", "GET").upper()
            status, payload = http_json(url, method, headers, body if method != "GET" else None)

            if status == 401:
                try:
                    token = login(config)
                    if token:
                        variables["token"] = token
                        headers = build_headers(config, variables)
                        status, payload = http_json(url, method, headers, body if method != "GET" else None)
                except Exception as e:
                    payload = {"login_retry_error": str(e), "prev": payload}

            expected = step.get("expected_response") or {}
            failures = []
            if not isinstance(payload, dict):
                failures.append(f"non-json response HTTP {status}")
            else:
                failures.extend(match_expected(payload, expected))
                extract = step.get("extract_vars") or {}
                if not failures:
                    for var_name, var_path in extract.items():
                        try:
                            variables[var_name] = str(get_by_path(payload, var_path))
                        except Exception:
                            failures.append(f"extract_vars {var_name}: missing {var_path}")

            step_ok = len(failures) == 0
            if not step_ok:
                case_pass = False

            step_reports.append({
                "name": step.get("name"),
                "method": method,
                "url": url,
                "request_body": body,
                "status_code": status,
                "pass": step_ok,
                "failures": failures,
                "response_preview": preview_response(payload),
            })
            line = f"[{'PASS' if step_ok else 'FAIL'}] {case_name} HTTP={status} failures={failures}"
            print(line.encode("ascii", "replace").decode("ascii"))

        if case_pass:
            passed += 1
            status_str = "passed"
        else:
            failed += 1
            status_str = "failed"

        report_cases.append({
            "name": case_name,
            "excel_keys": None,
            "status": status_str,
            "pass": case_pass,
            "steps": step_reports,
        })

    finished = datetime.now(timezone.utc)
    report = {
        "config": config.get("name"),
        "started_at": started.isoformat(),
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "cases": report_cases,
        "finished_at": finished.isoformat(),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    summary = f"total:{report['total']}  PASS:{report['passed']}  FAIL:{report['failed']}"
    print(summary)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
