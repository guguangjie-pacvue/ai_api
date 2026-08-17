"""
backfill_pct.py — 为缺失占比的旧 cases.json 回填「占比约xx%」
用法: python backfill_pct.py <cases.json>

对文件内每个接口(path)分组：
  1. 为每个 case 计算判别签名 (dim, non_us, 关键filter字段集)
  2. 查 ES 500 条，为每条记录计算同样签名，"最具体匹配优先"归类
  3. 算占比，回填该 case description 末尾的「占比约xx%（n次）」
"""
import json, os, re, base64, urllib.request
from collections import defaultdict

ES_URL   = "https://logs.pacvue.com/internal/search/es"
ES_AUTH  = base64.b64encode(b"watcher:kY9GErML%luQTorm").decode()
NOISE_FILTERS = {'ReportDateTime', 'AdGroupState', 'CampaignState', 'State',
                 'ServingStatus', 'TargetState', 'KeywordState', 'AdState'}

def es_query(endpoint_path, index='amazon-access-*', size=500):
    body = {"params": {"index": index, "body": {
        "query": {"bool": {"must": [{"function_score": {
            "query": {"bool": {
                "must": [
                    {"term": {"apiEndpoint.keyword": endpoint_path}},
                    {"term": {"method.keyword": "POST"}}
                ],
                "must_not": [{"term": {"userId.keyword": "18183"}}],
                "filter": [{"range": {"@timestamp": {"gte": "now-30d"}}}]
            }},
            "functions": [{"random_score": {}}], "boost_mode": "replace"
        }}]}},
        "size": size, "_source": ["body"], "sort": ["_score"]
    }}}
    req = urllib.request.Request(ES_URL, data=json.dumps(body).encode(),
        headers={"Authorization": "Basic " + ES_AUTH, "kbn-xsrf": "true",
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    out = []
    for h in data.get('rawResponse', {}).get('hits', {}).get('hits', []):
        raw = h.get('_source', {}).get('body')
        if not raw: continue
        try: out.append(json.loads(raw))
        except: pass
    return out

def signature(rb):
    dim = str(rb.get('Dim') or rb.get('dim') or '').lower()
    tomarket = rb.get('ToMarket') or rb.get('toMarket') or ''
    non_us = tomarket not in ('US', '', None)
    fnames = set()
    has_compare = False
    for f in (rb.get('Filters') or []):
        fn = f.get('filterFieldName') or f.get('FilterFieldName')
        if fn and fn not in NOISE_FILTERS:
            fnames.add(fn)
        # 对比列：ReportDateTime filterContent 里含 startCompare
        fc = f.get('filterContent') or f.get('FilterContent') or ''
        if isinstance(fc, str) and 'startCompare' in fc:
            has_compare = True
    # 额外判别维度
    mids = rb.get('MetricIds') or rb.get('metricIds')
    has_metrics = bool(mids)
    grp = rb.get('IsGroupByProfile') or rb.get('isGroupByProfile')
    is_group = bool(grp)
    same_sku = bool(rb.get('isSameSku') or rb.get('IsSameSku') or
                    rb.get('AsinGroupBy') or rb.get('asinGroupBy'))
    return (dim, non_us, frozenset(fnames), has_compare, has_metrics, is_group, same_sku)

def _extra_eq(a, b):
    # dim, non_us, compare, metrics, group, same_sku 全等（除 filterset[2]）
    return a[0] == b[0] and a[1] == b[1] and a[3:] == b[3:]

def classify(rec_sig, case_sigs):
    # 1. 完全相等
    for i, cs in enumerate(case_sigs):
        if cs == rec_sig:
            return i
    # 2. 其余判别维度全等 + case filterset ⊆ record filterset，取最具体
    best, best_n = None, -1
    for i, cs in enumerate(case_sigs):
        if _extra_eq(cs, rec_sig) and cs[2] <= rec_sig[2] and len(cs[2]) > best_n:
            best, best_n = i, len(cs[2])
    if best is not None:
        return best
    # 3. 放宽：仅 dim+non_us 相同、空 filter 的兜底 case
    for i, cs in enumerate(case_sigs):
        if cs[0] == rec_sig[0] and cs[1] == rec_sig[1] and len(cs[2]) == 0:
            return i
    return None

def backfill_file(cases_path):
    with open(cases_path, encoding='utf-8-sig') as f:
        cases = json.load(f)

    by_path = defaultdict(list)
    for i, c in enumerate(cases):
        raw = c['steps'][0].get('path', '')
        full = ('/api/' + raw) if not raw.startswith('/') else raw
        full = full.split('?')[0].replace('/api/../', '/api/')
        by_path[full].append(i)

    summary = []
    for endpoint, idxs in by_path.items():
        records = es_query(endpoint)
        if not records:
            print(f'  !! no ES records for {endpoint}')
            for i in idxs:
                summary.append((cases[i]['name'].split(' - ',1)[-1], 0, None))
            continue
        case_sigs = [signature(cases[i]['steps'][0].get('request_body', {})) for i in idxs]
        counts = defaultdict(int)
        total = 0
        for rec in records:
            total += 1
            local = classify(signature(rec), case_sigs)
            if local is not None:
                counts[local] += 1
        for local, i in enumerate(idxs):
            n = counts.get(local, 0)
            pct = round(n / total * 100, 1)
            desc = cases[i].get('description', '')
            desc = re.sub(r'(500条随机样本中)?占比约[\d.]+%[（(]?\d*[次)）]*。?\s*$', '', desc).rstrip()
            if desc and not desc.endswith('。'): desc += '。'
            cases[i]['description'] = desc + f'500条随机样本中占比约{pct}%（{n}次）。'
            summary.append((cases[i]['name'].split(' - ',1)[-1], n, pct))

    with open(cases_path, 'w', encoding='utf-8') as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    return summary

if __name__ == '__main__':
    import sys
    summary = backfill_file(sys.argv[1])
    for name, n, pct in summary:
        pcts = f'{pct:>5}%' if pct is not None else '  N/A'
        print(f'    {n:>3} ({pcts})  {name[:55]}')
