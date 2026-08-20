"""summarize_report.py — 汇总 report.json 结果（Phase 4.3）

按接口路径聚合 PASS/FAIL，快速定位哪个接口失败。

用法：
  python scripts/summarize_report.py <report.json>
"""
import json, sys
from collections import defaultdict

with open(sys.argv[1], encoding='utf-8') as f:
    r = json.load(f)

print(f'总计:{r["total"]}  PASS:{r["passed"]}  FAIL:{r["failed"]}')

by_api = defaultdict(lambda: {'p': 0, 'f': 0})
for c in r['cases']:
    api = c['name'].split(' - ')[0].replace('POST /api/', '')
    if c['status'] == 'passed':
        by_api[api]['p'] += 1
    else:
        by_api[api]['f'] += 1

for api, v in sorted(by_api.items()):
    print(f"{api:<55} PASS:{v['p']:>3}  FAIL:{v['f']:>3}")
