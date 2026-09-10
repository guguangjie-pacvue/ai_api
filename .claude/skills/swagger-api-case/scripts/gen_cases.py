"""
gen_cases.py — 按"场景规格"从 ES 样本自动生成 cases.json（Happy Path，占比≥阈值的真实场景全覆盖）
用法: python gen_cases.py <spec.json> <out_cases.json> [--min-pct 1.0]
spec 格式：
{
  "module": "Dashboard", "base_url": "{{WALMARTBASEURL}}", "samples_dir": "...",
  "endpoints": [
    {"method":"POST","path":"/api/Dashboard","desc":"首页Dashboard汇总指标",
     "dims":["campaignTagIds"],            # 划分维度；支持 "a.b" 嵌套、"k:presence"(仅看有无)、"pageInfo.pageIndex:paged"(首页/翻页)
     "keep_dates":false,                   # true 时不把日期变量化（周/月序号与日期强绑定的接口）
     "expected":{"code":200},              # 可选，默认 L1
     "min_pct":1.0}                        # 可选，覆盖全局阈值
  ]
}
"""
import json, sys, os, re, collections, copy

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}([ T].*)?$')
MDY_RE = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')


def get(o, path):
    cur = o
    for p in path.split('.'):
        if isinstance(cur, dict):
            cur = cur.get(p, '<MISSING>')
        else:
            return '<MISSING>'
    return cur


def dim_value(body, dim):
    mode = None
    if ':' in dim:
        dim, mode = dim.split(':', 1)
    v = get(body, dim)
    if mode == 'presence':
        return 'has' if v != '<MISSING>' and v is not None else 'none'
    if mode == 'paged':
        return 'first' if v in (1, '1', '<MISSING>', None) else 'paged'
    if isinstance(v, list):
        if not v:
            return '[]'
        if all(isinstance(x, (int, str)) and re.fullmatch(r'\d+', str(x)) for x in v):
            return '[ids+]'
        return '[' + ','.join(sorted(set(str(x) for x in v)))[:60] + ']'
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)[:100]
    return v


# ── 标签 ──────────────────────────────────────────────────────────────────
TAG_FIELDS = {'campaignTagIds': 'CampaignTag', 'tagIds': 'Tag', 'adGroupTagIds': 'AdGroupTag',
              'keywordTagIds': 'KeywordTag', 'itemTagIds': 'ItemTag', 'campaignIds': 'Campaign',
              'adGroupIds': 'AdGroup', 'CampaignTagIds': 'CampaignTag', 'TagIds': 'Tag'}
DIM_MAP = {0: 'dim=0(汇总)', 1: '按天(dim=1)', 2: '按周(dim=2)', 3: '按月(dim=3)', 4: 'dim=4'}


def label_for(dim, val):
    mode = None
    key = dim
    if ':' in dim:
        key, mode = dim.split(':', 1)
    leaf = key.split('.')[-1]
    if mode == 'presence':
        return f"含{leaf}" if val == 'has' else f"不含{leaf}"
    if mode == 'paged':
        return '首页' if val == 'first' else '翻页(pageIndex>1)'
    if leaf in TAG_FIELDS:
        n = TAG_FIELDS[leaf]
        if val == '[]':
            return f"无{n}过滤"
        if val == '<MISSING>' or val is None:
            return f"不传{leaf}"
        return f"按{n}过滤"
    if leaf == 'dim':
        try:
            return DIM_MAP.get(int(val), f"dim={val}")
        except Exception:
            return f"dim={val}"
    if leaf in ('orderBy', 'orderByField'):
        return f"按{val}排序"
    if leaf == 'pageSize':
        return f"每页{val}条"
    if leaf == 'pageIndex':
        return f"第{val}页"
    if leaf == 'lowHealthFilterList':
        return f"健康问题={str(val).strip('[]')}"
    if val == '<MISSING>':
        return f"不传{leaf}"
    if isinstance(val, bool):
        return f"{leaf}={'true' if val else 'false'}"
    return f"{leaf}={val}"


# ── 变量化 ────────────────────────────────────────────────────────────────
ID_LIST_VARS = {'profileids': '{{profile_id}}'}
ID_ITEM_VARS = {'campaigntagids': '{{campaign_tag_id}}', 'tagids': '{{campaign_tag_id}}',
                'adgrouptagids': '{{adgroup_tag_id}}', 'campaignids': '{{campaign_id}}',
                'adgroupids': '{{adgroup_id}}'}
ID_SCALAR_VARS = {'profileid': '{{profile_id_single}}', 'campaignid': '{{campaign_id}}',
                  'adgroupid': '{{adgroup_id}}', 'campaigntagid': '{{campaign_tag_id}}',
                  'adgrouptagid': '{{adgroup_tag_id}}'}


def variablize(o, key='', keep_dates=False, notes=None):
    if notes is None:
        notes = []
    lk = key.lower()
    if isinstance(o, dict):
        return {k: variablize(v, k, keep_dates, notes) for k, v in o.items()}
    if isinstance(o, list):
        if o and lk in ID_LIST_VARS and all(re.fullmatch(r'\d+', str(x)) for x in o):
            return ID_LIST_VARS[lk]
        if o and lk in ID_ITEM_VARS and all(re.fullmatch(r'\d+', str(x)) for x in o):
            return [ID_ITEM_VARS[lk]]
        if o and lk.endswith('ids') and all(re.fullmatch(r'\d+', str(x)) for x in o):
            notes.append(f"{key} 保留样本真实ID(样本非本账号，需人工核实)")
            return o
        return [variablize(x, key, keep_dates, notes) for x in o]
    if isinstance(o, str):
        if not keep_dates and DATE_RE.match(o):
            if 'compared' in lk or 'prev' in lk:
                return '{{date_cmp_start}}' if ('start' in lk or 'begin' in lk) else '{{date_cmp_end}}'
            if 'start' in lk or 'begin' in lk or 'from' in lk:
                return '{{date_start}}'
            return '{{date_end}}'
        if not keep_dates and MDY_RE.match(o):
            if 'compared' in lk or 'prev' in lk:
                return '{{date_cmp_start_mdy}}' if 'start' in lk else '{{date_cmp_end_mdy}}'
            if 'start' in lk or 'begin' in lk:
                return '{{date_start_mdy}}'
            return '{{date_end_mdy}}'
        if lk in ID_SCALAR_VARS and re.fullmatch(r'\d+', o):
            return ID_SCALAR_VARS[lk]
        return o
    if isinstance(o, int) and not isinstance(o, bool):
        if lk in ID_SCALAR_VARS:
            return ID_SCALAR_VARS[lk]
        return o
    return o


def load_samples(samples_dir, path):
    safe = path.strip('/').replace('/', '_').replace('{', '').replace('}', '')
    fp = os.path.join(samples_dir, safe + '.json')
    if not os.path.exists(fp):
        return None, []
    data = json.load(open(fp, encoding='utf-8'))
    bodies = []
    for h in data['hits']:
        b = h.get('body')
        if isinstance(b, str):
            try:
                b = json.loads(b) if b.strip() else {}
            except Exception:
                continue
        bodies.append({'body': b if b is not None else {}, 'src': h})
    return data['total'], bodies


def main():
    spec_p, out_p = sys.argv[1], sys.argv[2]
    min_pct_g = 1.0
    if '--min-pct' in sys.argv:
        min_pct_g = float(sys.argv[sys.argv.index('--min-pct') + 1])
    spec = json.load(open(spec_p, encoding='utf-8'))
    cases = []
    summary = []
    for ep in spec['endpoints']:
        method, path = ep['method'].upper(), ep['path']
        total, samples = load_samples(spec['samples_dir'], path)
        min_pct = ep.get('min_pct', min_pct_g)
        if not samples:
            summary.append((method, path, total, 0, '无样本'))
            continue
        dims = ep.get('dims', [])
        keep_dates = ep.get('keep_dates', False)
        groups = collections.OrderedDict()
        for s in samples:
            b = s['body']
            sig = tuple((d, dim_value(b, d) if isinstance(b, dict) else None) for d in dims)
            groups.setdefault(sig, []).append(s)
        N = len(samples)
        ordered = sorted(groups.items(), key=lambda kv: -len(kv[1]))
        n_case = 0

        def full_sig(b):
            return json.dumps(variablize(copy.deepcopy(b), keep_dates=keep_dates), ensure_ascii=False, sort_keys=True)

        for sig, members in ordered:
            pct = len(members) * 100 / N
            if pct < min_pct:
                continue
            cnt = collections.Counter(full_sig(m['body']) for m in members)
            best = cnt.most_common(1)[0][0]
            cand = [m for m in members if full_sig(m['body']) == best]
            us = [m for m in cand if isinstance(m['body'], dict) and str(m['body'].get('toMarket', 'US')).upper() == 'US']
            rep = (us or cand)[0]['body']
            notes = []
            body = variablize(copy.deepcopy(rep), keep_dates=keep_dates, notes=notes)
            labels = [label_for(d, v) for d, v in sig] if dims else []
            label = '+'.join(labels) if labels else ep.get('single_label', '默认调用')
            desc_notes = ('；'.join(sorted(set(notes))) + '。') if notes else ''
            name_leaf = path.rstrip('/').split('/')[-1]
            case = {
                "name": f"{method} {path} - {label}",
                "description": f"单接口测试：{method} {path}。{ep.get('desc', '')}。场景：{label}。{desc_notes}{N}条随机样本中占比约{pct:.1f}%({len(members)}次)。",
                "module": spec['module'], "granularity": "API", "since": "init", "last_modified": "init",
                "change_type": "NEW", "generated_by": "swagger-api-case",
                "steps": [{
                    "name": f"调用 {name_leaf} - {label}", "method": method, "base_url": spec['base_url'],
                    "path": re.sub(r'^/api/', '', path),
                    "request_body": {} if method == 'GET' else body,
                    "extract_vars": {},
                    "expected_response": copy.deepcopy(ep.get('expected', {"code": 200}))
                }]
            }
            cases.append(case)
            n_case += 1
        summary.append((method, path, total, n_case, f"{N}样本/{len(groups)}组"))
    json.dump(cases, open(out_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"generated {len(cases)} cases -> {out_p}")
    for s in summary:
        print(f"  {s[0]:<5} {s[1]:<70} hits={s[2]!s:<7} cases={s[3]:<3} {s[4]}")


if __name__ == '__main__':
    main()
