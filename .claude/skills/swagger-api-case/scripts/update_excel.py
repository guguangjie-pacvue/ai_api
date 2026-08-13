"""
update_excel.py  —  Phase 5 Excel 写入（模块汇总 + 场景覆盖）

Usage:
  python scripts/update_excel.py \\
    --cases   single-api/mainapi/Amazon.Advertising.Api/SupplementData/task-xxx/cases.json \\
    --report  single-api/mainapi/Amazon.Advertising.Api/SupplementData/task-xxx/report.json \\
    --endpoints single-api/endpoints-Amazon.Advertising.Api.json \\
    --swagger-title "Amazon.Advertising.Api" \\
    --module  "SupplementData"

写入两个目标：
  1. [模块汇总] sheet：Case数 / 通过率 / 接口覆盖率
  2. [Amazon.Advertising.Api] / [PacvueMainApi] 等 swagger sheet：场景覆盖列
"""
import argparse, json, re
from collections import defaultdict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

EXCEL_PATH = 'C:/AI engineering/single-api/ai_api/single-api/swagger_modules.xlsx'

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
def update_summary(wb, swagger_title, module, report, endpoints):
    ws = wb['模块汇总']

    api_total   = len([e for e in endpoints if e.get('tag') == module])
    case_paths  = {s['path'] for c in report['cases'] for s in c.get('steps', [])}
    api_covered = len(case_paths)

    summary_font = Font(bold=True)
    summary_fill = PatternFill('solid', fgColor='D9E1F2')

    cols = {}
    for name in ('Case数', '通过率', '接口覆盖率'):
        cols[name] = _find_or_create_col(ws, name, summary_font, summary_fill)

    total  = report['total']
    passed = report['passed']
    pass_rate = (str(round(passed / total * 100)) + '%') if total else 'N/A'
    coverage  = (str(round(api_covered / api_total * 100)) + '%'
                 + ' (' + str(api_covered) + '/' + str(api_total) + ')') if api_total else 'N/A'

    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 1).value == swagger_title and ws.cell(r, 2).value == module:
            ws.cell(r, cols['Case数'],    total).alignment    = Alignment(horizontal='center')
            ws.cell(r, cols['通过率'],    pass_rate).alignment = Alignment(horizontal='center')
            ws.cell(r, cols['接口覆盖率'], coverage).alignment  = Alignment(horizontal='center')
            print(f'[模块汇总] {swagger_title}/{module}: case={total}, pass={pass_rate}, coverage={coverage}')
            return
    print(f'[模块汇总] WARNING: row not found for {swagger_title}/{module}')

# ── Phase 5.2 — 场景覆盖列 ──────────────────────────────────────────────────
def update_scenario_col(wb, swagger_sheet, cases):
    if swagger_sheet not in wb.sheetnames:
        print(f'[场景覆盖] sheet "{swagger_sheet}" not found, skip')
        return

    ws  = wb[swagger_sheet]
    bdr = _thin_border()
    h_font = Font(bold=True, color='FFFFFF')
    h_fill = PatternFill('solid', fgColor='2E5F8A')

    # Build path → scenario lines
    path_scenarios = defaultdict(list)
    for c in cases:
        steps = c.get('steps', [])
        if not steps:
            continue
        raw_path  = steps[0].get('path', '')
        full_path = ('/api/' + raw_path) if not raw_path.startswith('/') else raw_path
        name = c.get('name', '')
        desc = c.get('description', '')

        label_raw = name.split(' - ', 1)[1] if ' - ' in name else name
        m = re.match(r'^(场景\d+)[_\-](.+)$', label_raw)
        label = (m.group(1) + ': ' + m.group(2).replace('_', ' ')) if m else label_raw.replace('_', ' ')

        pct_m = re.search(r'占比约([\d.]+%)', desc)
        pct   = pct_m.group(1) if pct_m else '?%'
        path_scenarios[full_path].append(label + ' — ' + pct)

    # Find path column
    path_col = next(
        (c for c in range(1, ws.max_column + 1)
         if '路径' in str(ws.cell(1, c).value or '') or
            'path' in str(ws.cell(1, c).value or '').lower()),
        None
    )
    if path_col is None:
        print(f'[场景覆盖] path column not found in {swagger_sheet}'); return

    scene_col = _find_or_create_col(ws, '场景覆盖', h_font, h_fill, width=72)

    updated = 0
    for r in range(2, ws.max_row + 1):
        path = ws.cell(r, path_col).value
        if path in path_scenarios:
            lines = path_scenarios[path]
            cell  = ws.cell(r, scene_col, '\n'.join(lines))
            cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
            cell.border    = bdr
            ws.row_dimensions[r].height = max(ws.row_dimensions[r].height or 15, len(lines) * 16)
            updated += 1

    print(f'[场景覆盖] {swagger_sheet}: updated {updated} rows')

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cases',          required=True)
    ap.add_argument('--report',         required=True)
    ap.add_argument('--endpoints',      required=True)
    ap.add_argument('--swagger-title',  required=True, dest='swagger_title')
    ap.add_argument('--module',         required=True)
    ap.add_argument('--excel',          default=EXCEL_PATH)
    args = ap.parse_args()

    with open(args.cases,     encoding='utf-8-sig') as f: cases     = json.load(f)
    with open(args.report,    encoding='utf-8-sig') as f: report    = json.load(f)
    with open(args.endpoints, encoding='utf-8-sig') as f: endpoints = json.load(f)

    wb = openpyxl.load_workbook(args.excel)
    update_summary(wb, args.swagger_title, args.module, report, endpoints)
    update_scenario_col(wb, args.swagger_title, cases)
    wb.save(args.excel)
    print('Excel saved:', args.excel)

if __name__ == '__main__':
    main()
