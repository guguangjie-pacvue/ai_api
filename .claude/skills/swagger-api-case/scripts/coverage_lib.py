"""
coverage_lib.py — 接口覆盖率计算的共享逻辑

从 update_excel.py 抽出，供 update_excel.py（写 Excel）和 export_coverage.py
（导出前端看板用的 coverage.json）共用，避免两处覆盖率口径不一致。
"""
import json


def norm_path(p, base_url=''):
    """把 cases.json 里的相对 path（不含/api前缀，走ROOTURL的接口也不含）补全成
    与 endpoints-*.json 的 path 同格式的绝对路径，便于跨数据源匹配。"""
    if not p:
        return p
    p = p.split('?', 1)[0]
    if p.startswith('/api/') or p.startswith('/'):
        return p if p.startswith('/api/') or 'ROOTURL' in base_url else '/api' + p
    if 'ROOTURL' in base_url:
        return '/' + p
    return '/api/' + p


def canon(p):
    """归一化：去 query、去 /api/ 前缀、数字ID/{占位} 段统一为 *，以便按端点模板匹配。"""
    if not p:
        return ''
    p = p.split('?', 1)[0]
    p = p.split('/api/', 1)[-1] if '/api/' in p else p.lstrip('/')
    segs = ['*' if (s.isdigit() or (s.startswith('{') and s.endswith('}'))) else s.lower()
            for s in p.split('/')]
    return '/'.join(segs)


def load_json(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def compute_module_coverage(cases, report, endpoints, module):
    """计算单个模块的接口覆盖率 + case 通过率。

    cases:     该模块 cases.json 的内容（list）
    report:    该模块 report.json 的内容（dict，含 total/passed）
    endpoints: 该 swagger 的 endpoints-<title>.json 全量接口清单（list）
    module:    模块名，对应 endpoints 里的 tag

    返回 dict：api_total / api_covered / coverage_pct / case_total / case_passed / pass_rate_pct
    """
    module_eps = [e for e in endpoints if e.get('tag') == module]
    api_total = len(module_eps)

    case_keys = {
        ((s.get('method') or '').upper(), canon(norm_path(s.get('path', ''), s.get('base_url', ''))))
        for c in cases for s in c.get('steps', [])
    }
    api_covered = len({
        ((e.get('method') or '').upper(), canon(e.get('path', '')))
        for e in module_eps
        if ((e.get('method') or '').upper(), canon(e.get('path', ''))) in case_keys
    })

    case_total = report.get('total', 0)
    case_passed = report.get('passed', 0)

    return {
        'api_total': api_total,
        'api_covered': api_covered,
        'coverage_pct': round(api_covered / api_total * 100) if api_total else None,
        'case_total': case_total,
        'case_passed': case_passed,
        'pass_rate_pct': round(case_passed / case_total * 100) if case_total else None,
    }
