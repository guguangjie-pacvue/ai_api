import json, re, sys, ssl, urllib.request, urllib.error, urllib.parse, time, datetime

ROOT="/Users/guangjie/Project/ai_api/"
import argparse
_ap=argparse.ArgumentParser(description="执行 single-api cases.json，产出 report.json")
_ap.add_argument("--cases", required=True)
_ap.add_argument("--config", default=ROOT+"single-api/config.json")
_ap.add_argument("--out", required=True)
_a=_ap.parse_args()
cfg=json.load(open(_a.config,encoding="utf-8-sig"))
cases=json.load(open(_a.cases,encoding="utf-8-sig"))
outp=_a.out
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

def post(url, body, headers, timeout=120, method="POST"):
    data = None if method=="GET" else json.dumps(body).encode()
    req=urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            raw=r.read()
            ctype=r.headers.get("Content-Type","")
            try:
                return r.status, json.loads(raw.decode() or "{}")
            except (UnicodeDecodeError, json.JSONDecodeError):
                return r.status, {"__binary__": True, "content_type": ctype, "size": len(raw)}
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors="replace")
        try: return e.code, json.loads(raw)
        except Exception: return e.code, {"__raw__": raw[:500]}
    except Exception as e:
        return 0, {"__err__": str(e)}

def login():
    a=cfg["auth"]
    h={"Content-Type":"application/json"}; h.update(a.get("headers") or {})
    st,r=post(a["login_url"], a["body"], h)
    tok=r
    for k in a["token_path"].split("."): tok=(tok or {}).get(k)
    if not tok: raise RuntimeError(f"login failed {st} {str(r)[:300]}")
    cfg["variables"]["token"]=a.get("token_prefix","")+tok
    print("re-login OK")

def subst(o, V):
    if isinstance(o,str):
        m=re.fullmatch(r"\{\{(\w+)\}\}", o)
        if m and m.group(1) in V: return V[m.group(1)]
        return re.sub(r"\{\{(\w+)\}\}", lambda x: str(V.get(x.group(1), x.group(0))), o)
    if isinstance(o,list): return [subst(i,V) for i in o]
    if isinstance(o,dict): return {k:subst(v,V) for k,v in o.items()}
    return o

def get_path(obj, path):
    cur = obj
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        if part.startswith("["):
            idx = int(part[1:-1])
            cur = cur[idx] if isinstance(cur, list) and -len(cur) <= idx < len(cur) else None
        else:
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur

def check(exp, resp):
    fails=[]
    for k,v in exp.items():
        if k=="$binary":
            is_bin = isinstance(resp,dict) and resp.get("__binary__") is True
            min_size = v.get("$min_size",1) if isinstance(v,dict) else 1
            if not is_bin: fails.append(f"$binary expected binary file response, got {json.dumps(resp,ensure_ascii=False)[:120]}")
            elif resp.get("size",0) < min_size: fails.append(f"$binary expected size>={min_size}, got {resp.get('size',0)}")
            continue
        if k=="$root":
            cur=resp
        else:
            cur=get_path(resp, k)
        if isinstance(v,dict):
            if "$not_empty" in v:
                ok = cur not in (None,"",[],{})
                if not ok: fails.append(f"{k} expected not_empty, got {json.dumps(cur,ensure_ascii=False)[:120]}")
            if "$is_array" in v:
                if not isinstance(cur,list): fails.append(f"{k} expected array, got {type(cur).__name__}")
        else:
            if cur!=v: fails.append(f"{k} expected {v}, got {json.dumps(cur,ensure_ascii=False)[:200]}")
    return fails

login()
V=cfg["variables"]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
report={"config":cfg["name"],"started_at":started,"total":len(cases),"passed":0,"failed":0,"skipped":0,"cases":[]}
for i,c in enumerate(cases,1):
    cres={"name":c["name"],"status":"passed","pass":True,"steps":[]}
    for s in c["steps"]:
        base=cfg["base_urls"][s["base_url"].strip("{} ")]
        path=subst(s["path"],V)
        url=base.rstrip("/")+"/"+path.lstrip("/")
        headers=subst(cfg["headers"],V); headers.setdefault("Content-Type","application/json")
        body=subst(s["request_body"],V)
        method=s.get("method","POST").upper()
        req_url=url
        if method=="GET" and body:
            req_url=url+"?"+urllib.parse.urlencode(body)
        t0=time.time(); st,resp=post(req_url, body, headers, method=method)
        if st==401:
            login(); V=cfg["variables"]; headers=subst(cfg["headers"],V)
            st,resp=post(req_url, body, headers, method=method)
        extract_vars=s.get("extract_vars") or {}
        for _retry in range(3):
            if not extract_vars or all(get_path(resp, p) is not None for p in extract_vars.values()):
                break
            time.sleep(3)
            st,resp=post(req_url, body, headers, method=method)
        fails=check(s["expected_response"], resp) if st and st<500 else [f"http {st}"]
        if st>=400: fails.append(f"http {st} {json.dumps(resp,ensure_ascii=False)[:200]}")
        sres={"name":s["name"],"method":s["method"],"url":req_url,"status_code":st,
              "ms":int((time.time()-t0)*1000),"pass":not fails,"failures":fails,
              "resp_code":resp.get("code") if isinstance(resp,dict) else None,
              "resp_keys":list(resp.keys())[:10] if isinstance(resp,dict) else None,
              "data_shape":(("list" if isinstance(resp.get("data"),list) else
                             ("dict:"+",".join(list(resp["data"].keys())[:8]) if isinstance(resp.get("data"),dict)
                              else type(resp.get("data")).__name__)) if isinstance(resp,dict) else None),
              "data_len":(len(resp["data"]) if isinstance(resp,dict) and isinstance(resp.get("data"),(list,dict)) else None),
              "msg":(resp.get("message") or resp.get("msg") or resp.get("__raw__") or resp.get("__err__")) if isinstance(resp,dict) else None}
        cres["steps"].append(sres)
        if fails: cres["status"]="failed"; cres["pass"]=False
        for var_name, var_path in (s.get("extract_vars") or {}).items():
            val = get_path(resp, var_path)
            if val is not None: V[var_name] = val
    report["cases"].append(cres)
    report["passed" if cres["pass"] else "failed"]+=1
    print(f"[{i:>2}/{len(cases)}] {'PASS' if cres['pass'] else 'FAIL'}  {c['name'][:75]}  {cres['steps'][0]['ms']}ms  {cres['steps'][0]['failures'][:1]}")
report["finished_at"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(report,open(outp,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(f"\nTOTAL {report['total']}  PASS {report['passed']}  FAIL {report['failed']}  -> {outp}")
