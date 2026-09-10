"""
enrich_assertions.py — 根据首轮 report.json 的 data_shape 给 cases.json 补 L2 断言（一层深度，保证断言真实生效）
用法: python enrich_assertions.py <cases.json> <report.json>
规则: data 为 list → {"data":{"$is_array":true}}; data 为 dict → {"data":{"$not_empty":true}}; None/其他 → 不加
"""
import json, sys

cases_p, report_p = sys.argv[1], sys.argv[2]
cases = json.load(open(cases_p, encoding='utf-8-sig'))
report = json.load(open(report_p, encoding='utf-8-sig'))
by_name = {c['name']: c for c in report['cases']}
changed = 0
for c in cases:
    r = by_name.get(c['name'])
    if not r:
        continue
    for i, st in enumerate(c['steps']):
        rs = r['steps'][i] if i < len(r['steps']) else None
        if not rs or rs.get('status_code') != 200 or rs.get('resp_code') != 200:
            continue
        shape = rs.get('data_shape') or ''
        exp = st['expected_response']
        if shape == 'list':
            exp['data'] = {"$is_array": True}
            changed += 1
        elif shape.startswith('dict'):
            exp['data'] = {"$not_empty": True}
            changed += 1
json.dump(cases, open(cases_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"enriched {changed} steps")
