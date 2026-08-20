"""fix_bom.py — 去除 PowerShell 生成文件的 UTF-8 BOM（Phase 4.1）

PowerShell 写出的 JSON 带 BOM，Python 的 json.load 会报错。执行 run-cases 前先跑本脚本重写为无 BOM UTF-8。

用法：
  python scripts/fix_bom.py <file1.json> [<file2.json> ...]
  # 典型：cases.json + config.json
"""
import json, sys

for f in sys.argv[1:]:
    with open(f, encoding='utf-8-sig') as r:
        d = json.load(r)
    with open(f, 'w', encoding='utf-8') as w:
        json.dump(d, w, ensure_ascii=False, indent=2)
    print('Fixed:', f)
