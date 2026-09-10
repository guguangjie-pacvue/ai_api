"""
fetch_es_profile_filtered.py — 按接口+目标profileId 查询ES真实入参(用于own-profile样本不足场景)
复用 backfill_pct.py 的凭据/连接，用 match_phrase 过滤 body 中的 profileId 字符串
用法: python fetch_es_profile_filtered.py <out_dir> <profile_id> <endpoint1> [<endpoint2> ...]
每个 endpoint 格式: METHOD:/path
"""
import json, sys, os, importlib.util, urllib.request

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("backfill_pct", os.path.join(_here, "backfill_pct.py"))
_backfill = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_backfill)

ES_URL = _backfill.ES_URL
ES_AUTH = _backfill.ES_AUTH
ES_INDEX = _backfill.ES_INDEX

def es_query_profile(endpoint_path, method, profile_id, size=200):
    body = {"params": {"index": ES_INDEX, "body": {
        "query": {"bool": {
            "must": [
                {"term": {"apiEndpoint.keyword": endpoint_path}},
                {"term": {"method.keyword": method}},
                {"match_phrase": {"body": profile_id}}
            ],
            "must_not": [{"term": {"userId.keyword": "18183"}}],
            "filter": [{"range": {"@timestamp": {"gte": "now-180d"}}}]
        }},
        "size": size, "_source": ["body", "queryString", "@timestamp"], "sort": [{"@timestamp": "desc"}]
    }}}
    req = urllib.request.Request(ES_URL, data=json.dumps(body).encode(),
        headers={"Authorization": "Basic " + ES_AUTH, "kbn-xsrf": "true",
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    return [h.get('_source', {}) for h in
            data.get('rawResponse', {}).get('hits', {}).get('hits', [])]

def main():
    out_dir = sys.argv[1]
    profile_id = sys.argv[2]
    endpoints = sys.argv[3:]
    os.makedirs(out_dir, exist_ok=True)
    for ep in endpoints:
        method, path = ep.split(":", 1)
        safe = path.strip("/").replace("/", "_")
        try:
            hits = es_query_profile(path, method, profile_id)
            out_path = os.path.join(out_dir, f"{safe}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(hits, f, ensure_ascii=False)
            print(f"{method} {path} => {len(hits)} hits -> {out_path}")
        except Exception as e:
            print(f"{method} {path} => ERROR: {e}")

if __name__ == "__main__":
    main()
