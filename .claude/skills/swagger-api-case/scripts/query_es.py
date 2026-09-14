#!/usr/bin/env python3
"""
query_es.py -- Python port of query_es.ps1 for environments without pwsh (e.g. macOS without PowerShell installed).

Usage:
  python3 query_es.py --index rule-api-access-* --path /config/RuleActionMetrics --method POST \
      --path-field urlReferrer.keyword [--platform instacart] [--client-id-exclude 62,3186] \
      [--size 500] [--days 90] [--count-only]

Behavior mirrors query_es.ps1:
  - Method=POST and --platform given -> add queryString: productLine=<platform> filter
  - Method=GET or no --platform -> no platform filter (GET queryString is empty)
Output:
  - Prints hit count to stderr
  - Prints each hit's _source.body as one JSON line to stdout (unless --count-only)
"""
import argparse
import base64
import json
import sys
import urllib.request

ES_USER = "watcher"
ES_PASS = "kY9GErML%luQTorm"
ES_URL = "https://logs.pacvue.com/internal/search/es"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--method", required=True)
    ap.add_argument("--path-field", required=True)
    ap.add_argument("--platform", default=None)
    ap.add_argument("--client-id-exclude", default="62,3186")
    ap.add_argument("--size", type=int, default=500)
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--count-only", action="store_true")
    args = ap.parse_args()

    client_id_exclude = [int(x) for x in args.client_id_exclude.split(",") if x.strip()]
    method_upper = args.method.upper()

    must = [
        {"term": {args.path_field: args.path}},
        {"term": {"method.keyword": method_upper}},
    ]
    if args.platform and method_upper == "POST":
        # NOTE: the ES index has no `queryString` field (verified empty on every
        # sampled doc), so the previously-documented `queryString:productLine=<platform>`
        # filter always returns 0 hits regardless of real traffic. The request body
        # itself carries `productLine` for endpoints where the platform is caller-supplied
        # (e.g. rule create/report endpoints) -- use that instead.
        must.append({"term": {"body.productLine.keyword": args.platform}})
        print(f"[query_es] POST + platform={args.platform} -> add body.productLine.keyword filter", file=sys.stderr)
    elif args.platform:
        print(f"[query_es] {method_upper} no platform filter (platform not distinguishable for GET) -> using all-platform traffic", file=sys.stderr)

    size = 0 if args.count_only else args.size
    body = {
        "params": {
            "index": args.index,
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "function_score": {
                                    "query": {
                                        "bool": {
                                            "must": must,
                                            "must_not": [{"terms": {"clientId": client_id_exclude}}],
                                            "filter": [{"range": {"@timestamp": {"gte": f"now-{args.days}d"}}}],
                                        }
                                    },
                                    "functions": [{"random_score": {}}],
                                    "boost_mode": "replace",
                                }
                            }
                        ]
                    }
                },
                "size": size,
                "_source": ["body", "@timestamp"],
                "sort": ["_score"],
            },
        }
    }

    token = base64.b64encode(f"{ES_USER}:{ES_PASS}".encode("ascii")).decode("ascii")
    req = urllib.request.Request(
        ES_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Basic {token}",
            "kbn-xsrf": "true",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    total = result["rawResponse"]["hits"]["total"]
    print(f"[query_es] {method_upper} {args.path} : {total} hits", file=sys.stderr)
    if not args.count_only:
        for hit in result["rawResponse"]["hits"]["hits"]:
            src = hit.get("_source", {})
            if "body" in src:
                print(json.dumps(src["body"]))
            else:
                print(json.dumps(None))


if __name__ == "__main__":
    main()
