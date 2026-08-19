"""
backfill_pct.py — 为 cases.json 回填「占比约xx%」（增/查/改/删全支持）
用法: python backfill_pct.py <cases.json>

按 (接口路径, HTTP方法) 分组，各组独立查 ES 近30天 500 条，统计每个 case 的真实调用占比：
  • 有 body 的接口（POST/PUT/DELETE 查询&写操作）→ 按 request_body 判别签名分类
  • GET 接口（body 为空，参数在 URL）      → 按 queryString 判别签名分类
回填到各 case description 末尾「500条随机样本中占比约xx%（n次）。」（幂等可重跑）

写操作（Create/Update/Delete/Bulk…）同样按其 endpoint 的真实调用频率统计——
单场景 endpoint 自然是 100%，多场景按 body 特征拆分。
"""
import json, os, re, base64, urllib.request
from collections import defaultdict

ES_URL   = "https://logs.pacvue.com/internal/search/es"
ES_AUTH  = base64.b64encode(b"watcher:kY9GErML%luQTorm").decode()
ES_INDEX = "amazon-access-*"  # 默认值，可通过 --es-index 覆盖
NOISE_FILTERS = {'ReportDateTime', 'AdGroupState', 'CampaignState', 'State',
                 'ServingStatus', 'TargetState', 'KeywordState', 'AdState'}

# ── ES 查询：按 endpoint + method 拉样本（含 body 与 queryString） ──────────────
def es_query(endpoint_path, method, size=500):
    body = {"params": {"index": ES_INDEX, "body": {
        "query": {"bool": {"must": [{"function_score": {
            "query": {"bool": {
                "must": [
                    {"term": {"apiEndpoint.keyword": endpoint_path}},
                    {"term": {"method.keyword": method}}
                ],
                "must_not": [{"term": {"userId.keyword": "18183"}}],
                "filter": [{"range": {"@timestamp": {"gte": "now-90d"}}}]
            }},
            "functions": [{"random_score": {}}], "boost_mode": "replace"
        }}]}},
        "size": size, "_source": ["body", "queryString"], "sort": ["_score"]
    }}}
    req = urllib.request.Request(ES_URL, data=json.dumps(body).encode(),
        headers={"Authorization": "Basic " + ES_AUTH, "kbn-xsrf": "true",
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    return [h.get('_source', {}) for h in
            data.get('rawResponse', {}).get('hits', {}).get('hits', [])]

# ── body 判别签名（POST/PUT/DELETE） ──────────────────────────────────────────
def body_signature(rb):
    dim = str(rb.get('Dim') or rb.get('dim') or '').lower()
    tomarket = rb.get('ToMarket') or rb.get('toMarket') or ''
    non_us = tomarket not in ('US', '', None)
    fnames = set()
    has_compare = False
    for f in (rb.get('Filters') or []):
        fn = f.get('filterFieldName') or f.get('FilterFieldName')
        if fn and fn not in NOISE_FILTERS:
            fnames.add(fn)
        fc = f.get('filterContent') or f.get('FilterContent') or ''
        if isinstance(fc, str) and 'startCompare' in fc:
            has_compare = True
    has_metrics = bool(rb.get('MetricIds') or rb.get('metricIds'))
    is_group = bool(rb.get('IsGroupByProfile') or rb.get('isGroupByProfile'))
    same_sku = bool(rb.get('isSameSku') or rb.get('IsSameSku') or
                    rb.get('AsinGroupBy') or rb.get('asinGroupBy'))
    # 写操作判别（增/改/删）：递归收集 matchType / type / state / 是否 adGroup 级
    mtypes, types, states, has_adg = _writeop_disc(rb)
    return ('body', dim, non_us, frozenset(fnames), has_compare, has_metrics,
            is_group, same_sku, mtypes, types, states, has_adg)

def _writeop_disc(rb):
    mtypes, types, states, has_adg = set(), set(), set(), False
    def walk(o):
        nonlocal has_adg
        if isinstance(o, dict):
            for k, v in o.items():
                kl = k.lower()
                if kl in ('matchtype', 'negativematchtype') and isinstance(v, str) and v:
                    mtypes.add(v)
                elif kl == 'type' and isinstance(v, (str, int)) and v != '':
                    types.add(str(v))
                elif kl == 'state' and isinstance(v, str) and v:
                    states.add(v)
                elif kl in ('adgroupid', 'adgroupids') and v:
                    has_adg = True
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(rb)
    return frozenset(mtypes), frozenset(types), frozenset(states), has_adg

# ── queryString 判别签名（GET） ───────────────────────────────────────────────
def qs_signature(qs):
    """把 '?isCheckEdit=1&campaignId=123456' 规范成参数集合。
       动态 id/日期 只保留参数名，枚举/布尔保留 名=值。"""
    if not qs:
        return ('qs', frozenset())
    toks = set()
    for part in str(qs).lstrip('?').split('&'):
        if not part:
            continue
        k, _, v = part.partition('=')
        v = v.replace('{{', '').replace('}}', '')
        if re.fullmatch(r'[\d]{6,}', v) or re.fullmatch(r'[\d/\-]{6,}', v):
            toks.add(k)                # id / 日期 → 只留参数名
        else:
            toks.add(f'{k}={v}')       # 枚举 / 布尔 → 名=值
    return ('qs', frozenset(toks))

def record_signature(source, is_get):
    if is_get:
        return qs_signature(source.get('queryString'))
    raw = source.get('body') or ''
    try:
        return body_signature(json.loads(raw))
    except Exception:
        return ('body', '', False, frozenset(), False, False, False, False)

def case_signature(case, is_get):
    step = case['steps'][0]
    if is_get:
        path = step.get('path', '')
        qs = path.split('?', 1)[1] if '?' in path else ''
        return qs_signature(qs)
    return body_signature(step.get('request_body', {}) or {})

# ── 归类：完全相等 → 子集最具体 → dim/非us兜底 ───────────────────────────────
def classify(rec_sig, case_sigs):
    for i, cs in enumerate(case_sigs):
        if cs == rec_sig:
            return i
    kind = rec_sig[0]
    if kind == 'qs':
        # GET：case 参数集 ⊆ 记录参数集，取最具体
        best, best_n = None, -1
        for i, cs in enumerate(case_sigs):
            if cs[0] == 'qs' and cs[1] <= rec_sig[1] and len(cs[1]) > best_n:
                best, best_n = i, len(cs[1])
        if best is not None:
            return best
        # 兜底：空/默认 queryString（如布尔默认 isCheckEdit=0 不带参）→ 归 query 最简的 case
        cand = [(len(cs[1]), i) for i, cs in enumerate(case_sigs) if cs[0] == 'qs']
        return min(cand)[1] if cand else None
    # body：其余判别维度全等 + filterset ⊆，取最具体
    def extra_eq(a, b):
        return a[1] == b[1] and a[2] == b[2] and a[4:] == b[4:]
    best, best_n = None, -1
    for i, cs in enumerate(case_sigs):
        if cs[0] == 'body' and extra_eq(cs, rec_sig) and cs[3] <= rec_sig[3] and len(cs[3]) > best_n:
            best, best_n = i, len(cs[3])
    if best is not None:
        return best
    for i, cs in enumerate(case_sigs):
        if cs[0] == 'body' and cs[1] == rec_sig[1] and cs[2] == rec_sig[2] and len(cs[3]) == 0:
            return i
    return None

def _write_pct(case, n, total):
    pct = round(n / total * 100, 1) if total else 0.0
    desc = case.get('description', '')
    desc = re.sub(r'(500条随机样本中)?占比约?[\d.]+%[（(]?\d*[次)）]*。?', '', desc).rstrip()
    if desc and not desc.endswith('。'):
        desc += '。'
    case['description'] = desc + f'500条随机样本中占比约{pct}%（{n}次）。'
    return pct

def backfill_file(cases_path, es_index=None):
    global ES_INDEX
    if es_index:
        ES_INDEX = es_index
    with open(cases_path, encoding='utf-8-sig') as f:
        cases = json.load(f)

    # 按 (无 query 的 path, method) 分组
    groups = defaultdict(list)
    for i, c in enumerate(cases):
        step = c['steps'][0]
        raw = step.get('path', '')
        full = ('/api/' + raw) if not raw.startswith('/') else raw
        endpoint = full.split('?')[0].replace('/api/../', '/api/')
        method = (step.get('method') or 'POST').upper()
        groups[(endpoint, method)].append(i)

    summary = []
    for (endpoint, method), idxs in groups.items():
        is_get = (method == 'GET')
        sources = es_query(endpoint, method)
        if not sources:
            print(f'  !! no ES records: {method} {endpoint}')
            for i in idxs:
                summary.append((cases[i]['name'].split(' - ', 1)[-1], 0, None))
            continue
        case_sigs = [case_signature(cases[i], is_get) for i in idxs]
        counts, total = defaultdict(int), 0
        for src in sources:
            total += 1
            local = classify(record_signature(src, is_get), case_sigs)
            if local is not None:
                counts[local] += 1
        # 同签名（无法从请求区分，多见于写操作构造场景）→ 均摊该 endpoint 调用量
        sig_groups = defaultdict(list)
        for local, cs in enumerate(case_sigs):
            sig_groups[cs].append(local)
        for cs, members in sig_groups.items():
            if len(members) < 2:
                continue
            tot = sum(counts.get(m, 0) for m in members)
            share, rem = divmod(tot, len(members))
            for j, m in enumerate(members):
                counts[m] = share + (1 if j < rem else 0)
        for local, i in enumerate(idxs):
            n = counts.get(local, 0)
            pct = _write_pct(cases[i], n, total)
            summary.append((cases[i]['name'].split(' - ', 1)[-1], n, pct))

    with open(cases_path, 'w', encoding='utf-8') as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    return summary

if __name__ == '__main__':
    import sys, argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('cases_path')
    ap.add_argument('--es-index', default=None, help='ES 索引，默认 amazon-access-*，rule-api 传 rule-access-*')
    args = ap.parse_args()
    for name, n, pct in backfill_file(args.cases_path, args.es_index):
        pcts = f'{pct:>5}%' if pct is not None else '  N/A'
        print(f'    {n:>3} ({pcts})  {name[:55]}')
