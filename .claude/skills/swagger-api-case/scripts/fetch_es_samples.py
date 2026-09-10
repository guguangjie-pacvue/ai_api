"""
fetch_es_samples.py — 按接口列表批量拉取 ES 真实入参样本，落盘为 jsonl 供场景分析
复用 backfill_pct.py 中已有的 es_query（避免重复内嵌凭据）
用法: python fetch_es_samples.py <out_dir> <endpoint1> [<endpoint2> ...]
每个 endpoint 格式: METHOD:/path
"""
import json, sys, os, importlib.util

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("backfill_pct", os.path.join(_here, "backfill_pct.py"))
_backfill = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_backfill)
es_query = _backfill.es_query

def main():
    out_dir = sys.argv[1]
    endpoints = sys.argv[2:]
    os.makedirs(out_dir, exist_ok=True)
    for ep in endpoints:
        method, path = ep.split(":", 1)
        safe = path.strip("/").replace("/", "_")
        try:
            hits = es_query(path, method)
            out_path = os.path.join(out_dir, f"{safe}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(hits, f, ensure_ascii=False)
            print(f"{method} {path} => {len(hits)} hits -> {out_path}")
        except Exception as e:
            print(f"{method} {path} => ERROR: {e}")

if __name__ == "__main__":
    main()
