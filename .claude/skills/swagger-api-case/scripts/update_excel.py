"""
update_excel.py  —  Phase 5 Excel 写入（模块汇总 + 场景覆盖）

Usage:
  python scripts/update_excel.py \\
    --cases   single-api/mainapi/us/Amazon.Advertising.Api/SupplementData/task-xxx/cases.json \\
    --report  single-api/mainapi/us/Amazon.Advertising.Api/SupplementData/task-xxx/report.json \\
    --endpoints single-api/endpoints-Amazon.Advertising.Api.json \\
    --swagger-title "Amazon.Advertising.Api" \\
    --module  "SupplementData" \\
    --env     us

写入两个目标：
  1. [模块汇总] sheet：Case数 / 通过率 / 接口覆盖率
  2. [Amazon.Advertising.Api] / [PacvueMainApi] 等 swagger sheet：场景覆盖列
"""
import argparse, json, re
from collections import defaultdict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from coverage_lib import norm_path, canon as _canon, compute_module_coverage

EXCEL_PATH = None  # 从 cases 路径自动推断：single-api/<服务>/swagger_modules.xlsx

# ── helpers ──────────────────────────────────────────────────────────────────
def _thin_border():
    s = Side(style='thin', color='BFBFBF')
    return Border(left=s, right=s, top=s, bottom=s)

def _find_or_create_col(ws, col_name, header_font=None, header_fill=None, width=None):
    for c in range(1, ws.max_column + 1):
        if ws.cell(1, c).value == col_name:
            return c
    col_idx = ws.max_column + 1
    cell = ws.cell(1, col_idx, col_name)
    if header_font:  cell.font  = header_font
    if header_fill:  cell.fill  = header_fill
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.border    = _thin_border()
    if width:
        ws.column_dimensions[get_column_letter(col_idx)].width = width
    return col_idx

# ── Phase 5.1 — 模块汇总 ─────────────────────────────────────────────────────
def update_summary(wb, swagger_title, module, env, cases, report, endpoints, module_path=None):
    ws = wb['模块汇总']

    # cases.json 的 step 只有相对 path（不含/api前缀），先用 norm_path 按 base_url 补全成
    # 绝对路径，再归一化按 (方法, 端点模板) 去重匹配；report.json 里的 step 只有完整 url
    # （含域名/服务前缀），不能直接拿来做路径匹配，因此改用 cases.json 作为匹配数据源。
    cov = compute_module_coverage(cases, report, endpoints, module)
    api_total, api_covered = cov['api_total'], cov['api_covered']

    summary_font = Font(bold=True)
    summary_fill = PatternFill('solid', fgColor='D9E1F2')

    # 找各列位置（按列名，顺序不固定）
    col_idx = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(1, c).value or ''
        if '环境' in v:        col_idx['env']      = c
        if 'Swagger' in v:    col_idx['swagger']   = c
        if 'Platform' in v:   col_idx['platform']  = c  # rule-api 多平台结构
        if 'Tag' in v:        col_idx['module']    = c
    for name in ('Case数', '通过率', '接口覆盖率'):
        col_idx[name] = _find_or_create_col(ws, name, summary_font, summary_fill)
    if module_path:
        col_idx['模块路径'] = _find_or_create_col(ws, '模块路径', summary_font, summary_fill, width=60)

    total  = cov['case_total']
    pass_rate = (str(cov['pass_rate_pct']) + '%') if cov['pass_rate_pct'] is not None else 'N/A'
    coverage  = (str(cov['coverage_pct']) + '%' + ' (' + str(api_covered) + '/' + str(api_total) + ')') \
                if cov['coverage_pct'] is not None else 'N/A'

    for r in range(2, ws.max_row + 1):
        # 环境列常为合并单元格（仅块首行有值，其余为 None）；None 视为继承块环境，不作否决
        env_val = ws.cell(r, col_idx['env']).value if 'env' in col_idx else None
        env_ok = env_val in (env, None, '')
        mod_ok  = 'module' in col_idx and ws.cell(r, col_idx['module']).value == module
        # 两列可能同时存在（如 rule-api 既有服务名又有平台名）：swagger_title 传的是
        # 实际调用方传入的那个值，按值匹配到对应的列，不预设固定优先级。
        # 多平台服务传的是平台名（如 tiktok），标准服务传的是 swagger 文档标题。
        if 'swagger' in col_idx and ws.cell(r, col_idx['swagger']).value == swagger_title:
            key_ok = True
        elif 'platform' in col_idx and ws.cell(r, col_idx['platform']).value == swagger_title:
            key_ok = True
        elif 'swagger' not in col_idx and 'platform' not in col_idx:
            key_ok = True  # 无 swagger/platform 列时仅按 module 匹配
        else:
            key_ok = False
        if env_ok and key_ok and mod_ok:
            ws.cell(r, col_idx['Case数'],    total).alignment    = Alignment(horizontal='center')
            ws.cell(r, col_idx['通过率'],    pass_rate).alignment = Alignment(horizontal='center')
            ws.cell(r, col_idx['接口覆盖率'], coverage).alignment  = Alignment(horizontal='center')
            if module_path and '模块路径' in col_idx:
                ws.cell(r, col_idx['模块路径'], module_path).alignment = Alignment(horizontal='left')
            print(f'[模块汇总] {swagger_title}/{module}[{env}]: case={total}, pass={pass_rate}, coverage={coverage}')
            return
    print(f'[模块汇总] WARNING: row not found for {swagger_title}/{module}[{env}]')

# ── Phase 5.2 — 接口级场景覆盖（单列「场景覆盖」，多行文本）────────────────────
def update_scenario_col(wb, swagger_sheet, env, cases, report, platform=None):
    if swagger_sheet not in wb.sheetnames:
        print(f'[场景覆盖] sheet "{swagger_sheet}" not found, skip')
        return

    ws  = wb[swagger_sheet]
    bdr = _thin_border()
    h_font = Font(bold=True, color='FFFFFF')
    h_fill = PatternFill('solid', fgColor='2E5F8A')

    norm = norm_path

    # Build (method, path) → scenario lines（从 cases 的 name/description 提取）
    method_path_scenarios = defaultdict(list)
    for c in cases:
        steps = c.get('steps', [])
        if not steps:
            continue
        # 优先从 case name 提取方法和路径（格式："{METHOD} /api/xxx - desc"）
        name_m = re.match(r'^([A-Z]+)\s+(/\S+)', c.get('name', ''))
        if name_m:
            case_method = name_m.group(1).upper()
            raw_path    = name_m.group(2)
            ref_step    = steps[0]
        else:
            # fallback: 取最后一步（实际被测接口）
            last = steps[-1]
            case_method = (last.get('method') or '').upper()
            raw_path    = last.get('path', '')
            ref_step    = last
        full_path = norm(raw_path, ref_step.get('base_url', ''))
        name = c.get('name', '')
        desc = c.get('description', '')
        label_raw = name.split(' - ', 1)[1] if ' - ' in name else name
        m = re.match(r'^(场景\d+)[_\-](.+)$', label_raw)
        label = (m.group(1) + ': ' + m.group(2).replace('_', ' ')) if m else label_raw.replace('_', ' ')
        pct_m = re.search(r'占比约([\d.]+%)', desc)
        if pct_m:
            entry = label + ' — ' + pct_m.group(1)
        elif '无ES流量' in desc or 'xx%' in desc:
            entry = label + '（无ES流量）'
        else:
            entry = label
        method_path_scenarios[(case_method, full_path)].append(entry)

    # 找列位置：方法列 + 接口路径列 + 既有「场景覆盖」列
    env_col  = next((c for c in range(1, ws.max_column + 1) if '环境' in str(ws.cell(1, c).value or '')), None)
    path_col = next((c for c in range(1, ws.max_column + 1)
                     if '路径' in str(ws.cell(1, c).value or '') or
                        'path' in str(ws.cell(1, c).value or '').lower()), None)
    method_col = next((c for c in range(1, ws.max_column + 1)
                       if str(ws.cell(1, c).value or '').strip().lower() in ('method', '方法', 'http方法')), None)
    platform_col = next((c for c in range(1, ws.max_column + 1)
                        if 'Platform' in str(ws.cell(1, c).value or '')), None)
    if path_col is None:
        print(f'[场景覆盖] path column not found in {swagger_sheet}'); return

    # 标准服务（mainapi/walmart）现在也有「平台(Platform)」列，但传入的 platform 参数其实
    # 是 swagger_title（不是真正的平台名），不会出现在该列的取值里；只有当 platform 参数
    # 确实是这个 sheet 用到的平台名之一（多平台服务，如 rule-api 传 tiktok）时才按列过滤，
    # 否则视为无平台概念，不过滤，行为等同于没有这一列。
    platform_values = {ws.cell(r, platform_col).value for r in range(2, ws.max_row + 1)} if platform_col else set()
    filter_by_platform = platform_col and platform in platform_values

    scene_col = _find_or_create_col(ws, '场景覆盖', h_font, h_fill, width=72)

    # 归一化索引：(method, canon_path) → entries
    canon_scenarios = {(meth, _canon(p)): v for (meth, p), v in method_path_scenarios.items()}

    updated = 0
    for r in range(2, ws.max_row + 1):
        if env_col and ws.cell(r, env_col).value not in (env, None, ''):
            continue
        # 多平台服务（rule-api）：必须按平台列过滤，否则会把当前平台的场景文本
        # 写到其它平台的同路径行上（历史 bug，曾导致 criteo 行显示 instacart 内容）。
        if filter_by_platform:
            row_platform = ws.cell(r, platform_col).value
            if row_platform != platform:
                continue
        path = ws.cell(r, path_col).value
        if not path:
            continue
        row_method = (ws.cell(r, method_col).value or '').strip().upper() if method_col else ''
        # 优先按 (method, path) 精确匹配；无方法列时退化为只按路径匹配
        lines = None
        if row_method:
            lines = (method_path_scenarios.get((row_method, path))
                     or canon_scenarios.get((row_method, _canon(path))))
        if lines is None:
            # 兼容无方法列的 sheet：合并所有方法的场景
            all_lines = []
            for (meth, p), v in method_path_scenarios.items():
                if p == path or _canon(p) == _canon(path):
                    all_lines.extend(v)
            lines = all_lines or None
        if lines:
            cell = ws.cell(r, scene_col, '\n'.join(lines))
            cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
            cell.border    = bdr
            ws.row_dimensions[r].height = max(ws.row_dimensions[r].height or 15, len(lines) * 16)
            updated += 1

    print(f'[场景覆盖] {swagger_sheet}[{env}]: updated {updated} rows')

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cases',          required=True)
    ap.add_argument('--report',         required=True)
    ap.add_argument('--endpoints',      required=True)
    ap.add_argument('--swagger-title',  required=True, dest='swagger_title')
    ap.add_argument('--sheet-name',     default=None,  dest='sheet_name',
                    help='场景覆盖 sheet 名，默认与 swagger-title 相同；多平台服务可单独指定（如 RuleApi）')
    ap.add_argument('--module',         required=True)
    ap.add_argument('--env',            default='us', choices=['us', 'cn', 'eu'])
    ap.add_argument('--excel',          default=None,
                    help='Excel 路径，默认从 cases 路径推断：single-api/<服务>/swagger_modules.xlsx')
    args = ap.parse_args()
    if not args.sheet_name:
        args.sheet_name = args.swagger_title

    # 自动推断 excel 路径：取 cases 路径中 single-api/<服务> 部分
    if not args.excel:
        import re as _re
        m = _re.match(r'(.*?single-api/[^/]+)/', args.cases.replace('\\', '/'))
        args.excel = (m.group(1) + '/swagger_modules.xlsx') if m else 'single-api/swagger_modules.xlsx'

    with open(args.cases,     encoding='utf-8-sig') as f: cases     = json.load(f)
    with open(args.report,    encoding='utf-8-sig') as f: report    = json.load(f)
    with open(args.endpoints, encoding='utf-8-sig') as f: endpoints = json.load(f)

    # 模块路径 = cases 路径去掉 /task-*/cases.json 的那一级模块目录，前缀 ai_api\，反斜杠
    # 用 rfind 定位仓库内的 single-api（仓库父目录本身也叫 single-api，绝对路径会出现两次）
    _norm = args.cases.replace('\\', '/')
    _i = _norm.rfind('single-api/')
    _rel = _norm[_i:] if _i >= 0 else _norm
    module_path = ('ai_api/' + '/'.join(_rel.split('/')[:-2])).replace('/', '\\')

    wb = openpyxl.load_workbook(args.excel)
    update_summary(wb, args.swagger_title, args.module, args.env, cases, report, endpoints, module_path)
    # swagger_title 对多平台服务（rule-api）传的就是平台名（如 criteo），用于按
    # 平台列过滤场景覆盖写入行；标准服务的 sheet 没有 Platform 列，此参数会被忽略。
    update_scenario_col(wb, args.sheet_name, args.env, cases, report, platform=args.swagger_title)
    # 原文件常被 Excel 打开占用：先存 tmp，再尝试替换；替换失败则保留 tmp 供手动合并
    import os, shutil
    tmp = args.excel.replace('.xlsx', '_tmp.xlsx')
    wb.save(tmp)
    try:
        shutil.move(tmp, args.excel)
        print('Excel saved:', args.excel)
    except PermissionError:
        print('Excel 被占用（请关闭后手动用 tmp 覆盖）。tmp 已保存:', tmp)

if __name__ == '__main__':
    main()
