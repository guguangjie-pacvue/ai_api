"""
es_batch.py — 批量统计/拉取 ES 样本（通用，参数化索引/路径字段/clientId 排除）
用法:
  count : python es_batch.py count  <endpoints.json> <tag1,tag2,...> <out.json> [--index walmart-access-*] [--days 365] [--exclude 0,62]
  fetch : python es_batch.py fetch  <out_dir> METHOD:/path [METHOD:/path ...] [--index ...] [--days 365] [--size 500] [--exclude 0,62]
"""
import json, sys, os, base64, urllib.request, time

ES_URL = "https://logs.pacvue.com/internal/search/es"
ES_AUTH = base64.b64encode(b"watcher:kY9GErML%luQTorm").decode()

def parse_opts(argv):
    opts = {"index": "walmart-access-*", "days": 365, "size": 500, "exclude": [0, 62], "path_field": "apiEndpoint.keyword"}
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            k = a[2:]; v = argv[i+1]; i += 2
            if k == "exclude": opts[k] = [int(x) for x in v.split(",")]
            elif k in ("days", "size"): opts[k] = int(v)
            else: opts[k] = v
        else:
            rest.append(a); i += 1
    return opts, rest

def es_search(path, method, opts, size):
    body = {"params": {"index": opts["index"], "body": {
        "query": {"bool": {"must": [{"function_score": {
            "query": {"bool": {
                "must": [{"term": {opts["path_field"]: path}}, {"term": {"method.keyword": method}}],
                "must_not": [{"terms": {"clientId": opts["exclude"]}}],
                "filter": [{"range": {"@timestamp": {"gte": f"now-{opts['days']}d"}}}]}},
            "functions": [{"random_score": {}}], "boost_mode": "replace"}}]}},
        "size": size, "_source": ["body", "@timestamp", "clientId", "userId"], "sort": ["_score"]}}}
    req = urllib.request.Request(ES_URL, data=json.dumps(body).encode(),
        headers={"Authorization": "Basic " + ES_AUTH, "kbn-xsrf": "true", "Content-Type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            hits = data.get("rawResponse", {}).get("hits", {})
            total = hits.get("total")
            if isinstance(total, dict): total = total.get("value")
            return total, [h.get("_source", {}) for h in hits.get("hits", [])]
        except Exception as e:
            if attempt == 2: raise
            time.sleep(2)

def main():
    mode = sys.argv[1]
    opts, rest = parse_opts(sys.argv[2:])
    if mode == "count":
        eps_file, tags, out = rest[0], rest[1].split(","), rest[2]
        eps = [e for e in json.load(open(eps_file, encoding="utf-8")) if e["tag"] in tags]
        result = []
        for e in eps:
            try:
                total, _ = es_search(e["path"], e["method"], opts, 0)
            except Exception as ex:
                total = f"ERROR:{ex}"
            result.append({"tag": e["tag"], "method": e["method"], "path": e["path"], "hits": total})
            print(f"{e['tag']:<16} {e['method']:<5} {e['path']:<70} {total}", flush=True)
        json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    elif mode == "fetch":
        out_dir = rest[0]; os.makedirs(out_dir, exist_ok=True)
        for ep in rest[1:]:
            method, path = ep.split(":", 1)
            safe = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
            total, hits = es_search(path, method, opts, opts["size"])
            json.dump({"total": total, "hits": hits}, open(os.path.join(out_dir, safe + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
            print(f"{method} {path} => total={total}, fetched={len(hits)}", flush=True)

if __name__ == "__main__":
    main()
