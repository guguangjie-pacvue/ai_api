"""
analyze_samples.py — 读取 es_batch.py fetch 落盘的样本，输出每个接口的变化字段与高频入参组合
用法: python analyze_samples.py <samples_dir> [file_substring_filter] [--top N] [--show-body]
"""
import json, sys, os, re, collections

def norm_val(k, v):
    """把动态值归一化成签名：日期→<DATE>，ID 数组→len，长数字→<NUM>"""
    if isinstance(v, bool): return v
    if v is None: return None
    if isinstance(v, (int, float)):
        if k.lower().endswith('id') or k.lower().endswith('ids') or v > 100000: return '<NUM>'
        return v
    if isinstance(v, str):
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}([ T].*)?', v) or re.fullmatch(r'\d{1,2}/\d{1,2}/\d{4}', v): return '<DATE>'
        if re.fullmatch(r'\d{5,}', v): return '<NUM>'
        return v if len(v) <= 40 else v[:37] + '...'
    if isinstance(v, list):
        if not v: return '[]'
        if all(isinstance(x, (int, str)) for x in v):
            if all(isinstance(x, int) or re.fullmatch(r'\d+', str(x)) for x in v): return '[ids+]'
            return '[' + ','.join(sorted(set(str(x) for x in v)))[:60] + ']' if len(v) <= 5 else f'[str×{len(v)}]'
        return f'[obj×{len(v)}]:' + json.dumps([norm_obj(x) for x in v[:2]], ensure_ascii=False, sort_keys=True)[:120]
    if isinstance(v, dict):
        return json.dumps(norm_obj(v), ensure_ascii=False, sort_keys=True)[:150]
    return str(v)

def norm_obj(o):
    if isinstance(o, dict): return {k: norm_val(k, v) for k, v in o.items()}
    return norm_val('', o)

def main():
    d = sys.argv[1]; flt = None; top = 8; show_body = False; ignore = set()
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--top': top = int(args[i+1]); i += 2
        elif args[i] == '--show-body': show_body = True; i += 1
        elif args[i] == '--ignore': ignore = set(args[i+1].split(',')); i += 2
        else: flt = args[i]; i += 1
    for fn in sorted(os.listdir(d)):
        if flt and flt.lower() not in fn.lower(): continue
        data = json.load(open(os.path.join(d, fn), encoding='utf-8'))
        hits = data['hits']; bodies = []
        for h in hits:
            b = h.get('body')
            if isinstance(b, str):
                try: b = json.loads(b) if b.strip() else {}
                except Exception: b = {'__raw__': b[:80]}
            bodies.append(b if b is not None else {})
        print(f"\n######## {fn}  total={data['total']} samples={len(hits)}")
        if not bodies: continue
        # 顶层字段变化
        if all(isinstance(b, dict) for b in bodies):
            keys = collections.Counter(k for b in bodies for k in b)
            varying = {}
            for k in keys:
                vals = collections.Counter(json.dumps(norm_val(k, b.get(k, '<MISSING>')), ensure_ascii=False, sort_keys=True) for b in bodies)
                if len(vals) > 1 and k not in ignore: varying[k] = vals
            print("  keys:", ', '.join(f"{k}({c})" for k, c in keys.most_common()))
            for k, vals in varying.items():
                print(f"  ~ {k}: " + ' | '.join(f"{v}={c}" for v, c in vals.most_common(6)) + (' ...' if len(vals) > 6 else ''))
            sigs = collections.Counter(json.dumps({k: norm_val(k, b.get(k)) for k in varying}, ensure_ascii=False, sort_keys=True) for b in bodies)
            print(f"  == 组合签名 top{top} (varying={list(varying)}):")
            for s, c in sigs.most_common(top): print(f"     {c:>4} {c*100/len(bodies):5.1f}%  {s[:400]}")
        else:
            sigs = collections.Counter(json.dumps(norm_obj(b), ensure_ascii=False, sort_keys=True) for b in bodies)
            for s, c in sigs.most_common(top): print(f"     {c:>4} {c*100/len(bodies):5.1f}%  {s[:400]}")
        if show_body:
            print("  -- sample body:", json.dumps(bodies[0], ensure_ascii=False)[:500])

if __name__ == '__main__':
    main()
