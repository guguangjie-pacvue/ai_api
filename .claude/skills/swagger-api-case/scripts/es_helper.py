#!/usr/bin/env python3
"""
es_helper.py -- extra ES query helpers for rule-api citrus single-api-case work,
complementing query_es.py for cases query_es.py can't handle:

1. Path-param endpoints (e.g. GET /definition/{ruleId}): query_es.py does an exact
   `term` match on urlReferrer.keyword, which never matches a templated path literally.
   Use `wildcard-agg` here to discover what real (ID-substituted) paths exist under a
   prefix, so you can tell genuine traffic from "ES 无流量".

2. Detecting whether an endpoint's body carries `productLine` at all (needed to decide
   whether a POST endpoint is platform-filterable via ES, or must fall back to
   all-platform traffic per services.json's `es.platform_filter.post_fallback_no_productline_field`).

3. Fetching literal samples for a resolved concrete path (once you know the real
   substituted value), with clientId visible so you can tell test-account vs real-customer traffic.

Usage:
  # 1) See what real paths exist under a prefix (excludes nothing; you must eyeball results
  #    to separate "ID leaf" hits from sibling static sub-routes already defined elsewhere in Swagger)
  python3 es_helper.py wildcard-agg --index rule-api-access-* --prefix /definition/ --method GET --days 90

  # 2) Check whether productLine field exists / has a citrus bucket for a given exact path+method
  python3 es_helper.py productline-agg --index rule-api-access-* --path /template/getTemplate --method POST --days 180

  # 3) Fetch N raw body samples for an exact path (literal, e.g. after resolving {ruleId}->real id),
  #    with clientId shown, optionally filtered by productLine
  python3 es_helper.py samples --index rule-api-access-* --path /definition/2098299714324836354 --method GET \
      --size 20 --days 180 [--platform citrus] [--client-id-exclude 62,3186] [--no-exclude-test]
"""
import argparse
import base64
import json
import sys
import urllib.request

ES_USER = "watcher"
ES_PASS = "kY9GErML%luQTorm"
ES_URL = "https://logs.pacvue.com/internal/search/es"


def _post(body):
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
        return json.loads(resp.read().decode("utf-8"))


def cmd_wildcard_agg(args):
    body = {
        "params": {
            "index": args.index,
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {"wildcard": {"urlReferrer.keyword": args.prefix + "*"}},
                            {"term": {"method.keyword": args.method.upper()}},
                        ],
                        "filter": [{"range": {"@timestamp": {"gte": f"now-{args.days}d"}}}],
                    }
                },
                "size": 0,
                "aggs": {"paths": {"terms": {"field": "urlReferrer.keyword", "size": args.size}}},
            },
        }
    }
    result = _post(body)
    total = result["rawResponse"]["hits"]["total"]
    buckets = result["rawResponse"]["aggregations"]["paths"]["buckets"]
    print(f"total={total}")
    for b in buckets:
        print(f"{b['doc_count']:>8}  {b['key']}")


def cmd_productline_agg(args):
    body = {
        "params": {
            "index": args.index,
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"urlReferrer.keyword": args.path}},
                            {"term": {"method.keyword": args.method.upper()}},
                        ],
                        "filter": [{"range": {"@timestamp": {"gte": f"now-{args.days}d"}}}],
                    }
                },
                "size": 0,
                "aggs": {"pl": {"terms": {"field": "body.productLine.keyword", "size": 50}}},
            },
        }
    }
    result = _post(body)
    total = result["rawResponse"]["hits"]["total"]
    buckets = result["rawResponse"]["aggregations"]["pl"]["buckets"]
    print(f"total={total}")
    if not buckets:
        print("NO_PRODUCTLINE_FIELD (empty buckets despite total>0) -> use all-platform traffic per fallback rule"
              if total else "NO_HITS_AT_ALL")
    for b in buckets:
        print(f"{b['doc_count']:>8}  {b['key']}")


def cmd_samples(args):
    must = [
        {"term": {"urlReferrer.keyword": args.path}},
        {"term": {"method.keyword": args.method.upper()}},
    ]
    if args.platform:
        must.append({"term": {"body.productLine.keyword": args.platform}})
    must_not = []
    if not args.no_exclude_test:
        excl = [int(x) for x in args.client_id_exclude.split(",") if x.strip()]
        must_not.append({"terms": {"clientId": excl}})
    body = {
        "params": {
            "index": args.index,
            "body": {
                "query": {"bool": {"must": must, "must_not": must_not,
                                    "filter": [{"range": {"@timestamp": {"gte": f"now-{args.days}d"}}}]}},
                "size": args.size,
                "_source": ["body", "clientId", "@timestamp"],
                "sort": [{"@timestamp": "desc"}],
            },
        }
    }
    result = _post(body)
    hits = result["rawResponse"]["hits"]
    print(f"total={hits['total']}", file=sys.stderr)
    for h in hits["hits"]:
        print(json.dumps(h["_source"]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("wildcard-agg")
    p1.add_argument("--index", required=True)
    p1.add_argument("--prefix", required=True)
    p1.add_argument("--method", required=True)
    p1.add_argument("--days", type=int, default=90)
    p1.add_argument("--size", type=int, default=50)
    p1.set_defaults(func=cmd_wildcard_agg)

    p2 = sub.add_parser("productline-agg")
    p2.add_argument("--index", required=True)
    p2.add_argument("--path", required=True)
    p2.add_argument("--method", required=True)
    p2.add_argument("--days", type=int, default=180)
    p2.set_defaults(func=cmd_productline_agg)

    p3 = sub.add_parser("samples")
    p3.add_argument("--index", required=True)
    p3.add_argument("--path", required=True)
    p3.add_argument("--method", required=True)
    p3.add_argument("--platform", default=None)
    p3.add_argument("--size", type=int, default=20)
    p3.add_argument("--days", type=int, default=180)
    p3.add_argument("--client-id-exclude", default="62,3186")
    p3.add_argument("--no-exclude-test", action="store_true")
    p3.set_defaults(func=cmd_samples)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
