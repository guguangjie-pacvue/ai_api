---
name: swagger-api-case
description: 单接口测试 case 生成。以 Swagger 为接口定义基线，从 ES 日志中抽取真实参数样本，生成单接口测试 case（覆盖正常路径 + 异常路径），输出到 single-api/task-<timestamp>/cases.json。当用户要"针对某个接口生成测试 case"、"基于 Swagger 生成接口测试"时使用本 skill。
---

# swagger-api-case（单接口测试 Case 生成）

## 定位

与 `api-case-generate` 的区别：

| | api-case-generate | swagger-api-case |
|---|---|---|
| 输入来源 | 前端源码扫描 | Swagger 定义 + ES 日志 |
| 粒度 | 业务流程（多接口链） | **单接口** |
| 场景 | 用户操作路径 | 正常路径 + 参数异常路径 |
| 产物目录 | `api-case-work/task-*/` | `single-api/task-*/` |

---

## 🔴 铁律

1. **Swagger 是结构权威**：字段类型、必填性、枚举值以 Swagger 为准，ES 只提供真实值样本
2. **禁止猜参数值**：无 Swagger example 且 ES 无样本的字段，值填 `"[NEEDS_REAL_VALUE]"` 并在末尾列出待补清单
3. **动态 ID 必须变量化**：数字 ID / timestamp 替换为 `{{var}}`，不得硬编码
4. **每次新建目录**：`single-api/task-<YYYY-MM-DD-HH-MM-SS>/`，禁止复用
5. **产物只有 cases.json 和 endpoints.json**：禁止生成其他文件

---

## 输入（运行时向用户逐步确认）

**第一步：用户提供 Swagger URL**

用户只需提供一个或多个 Swagger 文档的 URL（index.html 或 swagger.json 均可），无需事先指定接口。

**第二步：完成 Swagger 扫描后，向用户确认要查哪个服务**

ES 连接信息已固定，无需用户每次提供：
- **Kibana 地址**：`https://logs.pacvue.com`
- **用户名**：`watcher`
- **密码**：`kY9GErML%luQTorm`
- **访问方式**：PowerShell `Invoke-RestMethod` + Basic Auth

🔴 **只需向用户提问一项：**

> "请告诉我要查哪个服务的日志（服务名 / 索引关键字 / 环境，如 amazon-advertising-api、us-prod 等）"

收到后执行 Phase 2。

---

## Phase 0 — 获取并扫描 Swagger 文档

### 0.1 获取 swagger.json

对每个用户提供的 Swagger URL，推断其 JSON spec 地址并下载：

- 若 URL 以 `/swagger/index.html` 结尾 → 替换为 `/swagger/v1/swagger.json`
- 若 URL 已是 `.json` 结尾 → 直接使用

**HTTPS URL**：用 `WebFetch` 获取。

**HTTP URL（含内网 EC2 等）**：WebFetch 会强制升级为 HTTPS 导致失败，必须改用 PowerShell `WebClient` 下载：

```powershell
$client = New-Object System.Net.WebClient
$client.DownloadFile("<swagger_json_url>", "$env:TEMP\swagger_<服务名>.json")
Write-Host "Downloaded OK, size: $((Get-Item "$env:TEMP\swagger_<服务名>.json").Length)"
```

### 0.2 解析有效接口，去除 deprecated

下载完成后，用 Node.js 解析（PowerShell 的 `ConvertFrom-Json` 对大文件会失败，禁止使用）：

```powershell
node -e "
const fs = require('fs');
const spec = JSON.parse(fs.readFileSync(process.env.TEMP + '/swagger_<服务名>.json', 'utf8'));
const paths = spec.paths || {};
const rows = [];
for (const [path, methods] of Object.entries(paths)) {
    for (const [method, op] of Object.entries(methods)) {
        if (['get','post','put','delete','patch'].includes(method) && !op.deprecated) {
            const tag = (op.tags && op.tags[0]) || '(no tag)';
            const summary = op.summary || '';
            rows.push({ tag, method: method.toUpperCase(), path, summary });
        }
    }
}
rows.sort((a,b) => a.tag.localeCompare(b.tag) || a.path.localeCompare(b.path));
console.log(JSON.stringify(rows, null, 2));
"
```

### 0.3 将有效接口写入 endpoints.json

将解析结果写入 `single-api/endpoints-<title>.json`，格式：

```json
[
  { "tag": "Campaign", "method": "POST", "path": "/api/Campaign/GetCampaignPageData", "summary": "" },
  ...
]
```

**写入规则**：
- 若 `single-api/` 目录不存在，先创建
- **文件名取 Swagger spec 的 `info.title` 字段**，如 `endpoints-PacvueMainApi.json`、`endpoints-Amazon.Advertising.Api.json`
- 每次运行**覆盖**同名文件（endpoints 反映最新 Swagger 状态）
- 写入后在对话中输出按模块分组的汇总表：`模块 | 接口数`，供用户选择目标接口

---

## Phase 1 — 从 Swagger 提取目标端点定义

用户从汇总表中指定目标接口（module + path），再执行此步。

1. 从已下载的 `$env:TEMP\swagger_<服务名>.json` 中定位 `endpoint_path` + `endpoint_method`
2. 提取参数结论表（每个字段一行，一行不能漏）：

| 字段路径 | 位置(in) | 类型 | 必填 | 枚举值 | Swagger 示例值 | 说明 |
|----------|---------|------|------|--------|---------------|------|

- `in` = `path` / `query` / `header` / `body`（requestBody 里的字段写 `body`）
- 嵌套对象展开到叶子字段（如 `pageInfo.pageSize`）
- 有 `example` / `x-example` / `default` 的优先记录

3. 提取 Response 200 schema，列出关键返回字段（用于 L2 断言）

**🔴 结论表填完才能进 Phase 2，不得跳过。**

---

## Phase 2 — ES 日志抽取真实入参

**目标**：从生产日志中拿近 30 天用户的真实请求体，直接作为 case 的 `request_body`，不推断、不猜值。Swagger 负责结构校验，ES 负责提供真实数据。

### 2.1 已确认字段映射（amazon-access-* 已验证）

| 用途 | 字段名 |
|------|--------|
| 接口路径 | `apiEndpoint.keyword` |
| HTTP 方法 | `method.keyword` |
| 请求体 | `body`（JSON 字符串） |
| 时间戳 | `@timestamp` |

其他服务索引首次使用时，通过以下方式探测字段：
```powershell
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("watcher:kY9GErML%luQTorm"))
$headers = @{ "Authorization" = "Basic $b64"; "kbn-xsrf" = "true" }
Invoke-RestMethod -Uri "https://logs.pacvue.com/api/index_patterns/_fields_for_wildcard?pattern=<索引名>&meta_fields=_source" -Headers $headers | ConvertTo-Json -Depth 3
```

### 2.2 查询目标接口日志

🔴 **必须走 `/internal/search/es`，直接访问 `/elasticsearch/` 会 404**

```powershell
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("watcher:kY9GErML%luQTorm"))
$headers = @{ "Authorization" = "Basic $b64"; "kbn-xsrf" = "true"; "Content-Type" = "application/json" }
$body = @"
{"params":{"index":"<索引名，如 amazon-access-*>","body":{
  "query":{"bool":{"must":[
    {"function_score":{
      "query":{"bool":{
        "must":[
          {"term":{"apiEndpoint.keyword":"<endpoint_path>"}},
          {"term":{"method.keyword":"<METHOD>"}}
        ],
        "must_not":[{"term":{"userId.keyword":"18183"}}],
        "filter":[{"range":{"@timestamp":{"gte":"now-30d"}}}]
      }},
      "functions":[{"random_score":{}}],
      "boost_mode":"replace"
    }}
  ]}},
  "size":500,
  "_source":["body","@timestamp"],
  "sort":["_score"]
}}}
"@
$result = Invoke-RestMethod -Uri "https://logs.pacvue.com/internal/search/es" -Method POST -Headers $headers -Body $body -TimeoutSec 30
$result.rawResponse.hits.hits | ForEach-Object { $_._source.body | ConvertFrom-Json }
```

🔴 **`must_not userId=18183` 固定保留**，过滤测试账号数据，防止污染场景分析。

取出的每条记录即为真实入参，进入 2.3 分析。

### 2.3 分析真实入参，归纳用户场景

🔴 **不得直接用频率统计替代场景分析**。要阅读每条入参的实际内容，理解用户在做什么操作，再归纳成有业务意义的场景。

**分析维度**（逐条阅读入参后归纳）：

| 维度 | 看什么 |
|------|--------|
| 核心过滤组合 | Filters 里用了哪些 filterFieldName，决定用户的筛选意图 |
| 数 据维度| `Dim` 字段（ytd=汇总、date=趋势/逐日） |
| 分页/排序 | `pageSize` + `orderBy` 决定是列表浏览还是数据导出 |
| 特殊开关 | `IsFead`、`IsShowNTB` 等业务标志位的不同取值 |
| 市场 | `ToMarket` 是否有非 US 的真实用法 |

**归纳输出格式**（每个场景一段）：

```
### 场景N：<业务描述>
特征：<关键字段组合>
代表条数：[编号列表]，占比约 xx%
含义：<用户在界面上做了什么操作>
```

**归纳完成后**，每个场景对应一个 Happy Path case，用该场景的真实入参（动态字段变量化）填写 `request_body`。场景数即 Happy Path case 数，一一对应，不合并、不删减。

- ES 查询失败或无结果：记录原因，告知用户，终止本次生成

---

## Phase 3 — 生成 cases.json

**创建目录**：`single-api/task-<YYYY-MM-DD-HH-MM-SS>/`

**只生成 Happy Path case，每个真实用户场景对应一个 case。不生成异常、边界、缺失字段等额外 case。**

**🔴 ES 入参处理规则**：
- 数字型 ID（profileId、campaignId 等）→ 替换为 `{{profile_id}}`、`{{campaign_id}}` 等 config 变量
- 日期字段 → 替换为 `{{date_start_mdy}}`、`{{date_end_mdy}}` 等运行时变量
- `ToMarket` / `toMarket` → **保留 ES 真实值，不做变量化**（体现真实市场分布）
- 其余字段保持 ES 原始值不变，不推断、不替换

**断言规则**：

🔴 **`status_code: 200` 不能作为接口正常的标准**，HTTP 200 只代表网络层通，服务端可能返回业务错误。**必须用 `code: 200` 判断接口是否真正成功**。

**L1（强制）**：
```json
{"code": 200, "success": true}
```
不加 `status_code`，或仅作为辅助参考。

**L2（基于实际响应结构，Phase 4 探测后补充）**：
- 返回结构为 `data: {list:[], pageInfo:{}}` → 加 `"data.pageInfo": {"$not_empty": true}`
- 返回结构为 `data: []`（数组）→ 加 `"data": {"$is_array": true}`
- 返回结构为 `data: {...}`（对象，非分页）→ 加 `"data": {"$not_empty": true}`
- 不断言数据条数（测试账号可能空数据，`$length_gte:1` 不适用）

**JSON Schema**（严格遵守）：

```json
[
  {
    "name": "POST /api/xxx - <场景描述>",
    "description": "单接口测试：<method> <path>。<场景说明>。500条随机样本中占比xx%(n次)。",
    "module": "<从路径首段推断，如 Campaign>",
    "granularity": "API",
    "since": "init",
    "last_modified": "init",
    "change_type": "NEW",
    "generated_by": "swagger-api-case",
    "steps": [
      {
        "name": "调用 <接口末段名>",
        "method": "<METHOD>",
        "base_url": "{{BASEURL}}",
        "path": "<path>",
        "request_body": {},
        "extract_vars": {},
        "expected_response": {
          "code": 200,
          "success": true
        }
      }
    ]
  }
]
```

**base_url 选择规则**（参照 `api-case-work/config.json`）：

| 路径特征 | base_url 变量 |
|---------|--------------|
| `/api/` 开头（MainApi） | `{{BASEURL}}` |
| `amazon-advertising-api` 服务 | `{{INDBASEURL}}` |
| `/meta-api-` | `{{META}}` |
| `/micro-api-v2/` | `{{DAYPARTING}}` |
| `/filter-column/` | `{{FILTER_COLUMN}}` |
| `/ai-api/` | `{{AIURL}}` |

**断言规则**：见上方"Phase 3 断言规则"，`status_code` 已移除，以 `code: 200` + `success: true` 为接口成功标准。

---

---

## Phase 4 — 执行 cases.json 并产出 report.json

### 4.1 前置：去除 BOM

PowerShell 生成的文件带 UTF-8 BOM，Python 的 `json.load` 会报错，执行前必须先修复：

```bash
python -c "
import json
for f in ['single-api/task-<timestamp>/cases.json', 'single-api/config.json']:
    with open(f, encoding='utf-8-sig') as r: d = json.load(r)
    with open(f, 'w', encoding='utf-8') as w: json.dump(d, w, ensure_ascii=False, indent=2)
    print('Fixed:', f)
"
```

### 4.2 执行

```bash
python .claude/skills/api-case-generate/api-case-run/scripts/run-cases.py \
  --cases single-api/task-<timestamp>/cases.json \
  --config single-api/config.json \
  --out    single-api/task-<timestamp>/report.json
```

🔴 **注意事项**：
- `--config` 必须指向 `single-api/config.json`，不得用默认的 `api-case-work/config.json`
- cases 的 `path` 字段**不含 `/api/` 前缀**（已在生成时去掉），`INDBASEURL` 末尾有 `/api/`，两者拼接才正确
- token 会过期（约 10 小时），执行前确认 config.json 里 token 有效；脚本检测到 401 会自动用 `auth` 配置重新登录

### 4.3 分析结果

```bash
python -c "
import json
with open('single-api/task-<timestamp>/report.json', encoding='utf-8') as f:
    r = json.load(f)
print(f'总计:{r[\"total\"]}  PASS:{r[\"passed\"]}  FAIL:{r[\"failed\"]}')
from collections import defaultdict
by_api = defaultdict(lambda: {'p':0,'f':0})
for c in r['cases']:
    api = c['name'].split(' - ')[0].replace('POST /api/','')
    if c['status']=='passed': by_api[api]['p']+=1
    else: by_api[api]['f']+=1
for api,v in sorted(by_api.items()):
    print(f\"{api:<55} PASS:{v['p']:>3}  FAIL:{v['f']:>3}\")
"
```

**常见失败原因**：

| 现象 | 原因 | 处理 |
|------|------|------|
| HTTP 400 | 请求体结构异常（Filters 反序列化失败） | 删除该场景的 case |
| HTTP 200 但 FAIL | `data` 返回空列表，`$not_empty` 断言不过 | 断言改为 `$is_array` 允许空 |
| HTTP 401 | token 过期 | 重新登录刷新 token |
| HTTP 403 `toMarket contains illegal characters` | `{{to_market}}` 变量未替换（不经 run-cases.py 直接发请求时出现） | 必须通过 run-cases.py 执行 |

---

## 交付物

| 文件 | 说明 |
|------|------|
| `single-api/endpoints-<info.title>.json` | 当前 Swagger 全量有效接口列表，文件名取 spec 的 `info.title`（每次覆盖） |
| `single-api/task-<timestamp>/cases.json` | 目标接口的测试 case |
| `single-api/task-<timestamp>/report.json` | 执行结果报告 |
| `single-api/config.json` | 执行环境配置（token、profile_id、base_urls 等） |

对话中额外输出**待补清单**（若有 `[NEEDS_REAL_VALUE]` 字段）。
