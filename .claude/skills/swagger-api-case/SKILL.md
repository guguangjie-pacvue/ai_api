---
name: swagger-api-case
description: 单接口测试 case 生成。以 Swagger 为接口定义基线，从 ES 日志中抽取真实参数样本，生成单接口测试 case（覆盖正常路径 + 异常路径），输出到 single-api/<服务>/<swagger>/<模块>/task-<timestamp>/cases.json。当用户要"针对某个接口生成测试 case"、"基于 Swagger 生成接口测试"时使用本 skill。
---

# swagger-api-case（单接口测试 Case 生成）

## 定位

与 `api-case-generate` 的区别：

| | api-case-generate | swagger-api-case |
|---|---|---|
| 输入来源 | 前端源码扫描 | Swagger 定义 + ES 日志 |
| 粒度 | 业务流程（多接口链） | **单接口** |
| 场景 | 用户操作路径 | 正常路径 + 参数异常路径 |
| 产物目录 | `api-case-work/task-*/` | `single-api/<服务>/<swagger>/<模块>/task-*/` |

---

## 🔴 目录结构（强制）

**标准服务**（如 mainapi）：
```
single-api/
├── endpoints-<info.title>.json              # 每个 Swagger 一份全量接口列表（放根目录）
└── <服务>/                                   # 服务目录，如 mainapi
    └── <环境>/                               # 🔴 环境层：us / cn / eu
        ├── config.json                       # 🔴 环境级配置：token / profile_id / base_urls / auth
        └── <swagger>/                        # swagger 层，取 info.title，如 Amazon.Advertising.Api / PacvueMainApi
            └── <模块>/                       # 模块目录，如 Target / Targeting / Campaign
                └── task-<YYYY-MM-DD-HH-MM-SS>/
                    ├── cases.json
                    └── report.json
```

**多平台服务**（如 rule-api，平台参数存在时多加一层）：
```
single-api/
└── rule-api/
    └── <平台>/                               # 🔴 平台层：amazon / tiktok / walmart 等
        └── <环境>/                           # 环境层：us / cn / eu
            ├── config.json                   # 环境+平台级配置
            └── <模块>/                       # 模块目录，如 Definition / Template / History
                └── task-<YYYY-MM-DD-HH-MM-SS>/
                    ├── cases.json
                    └── report.json
```

- **标准服务五层：服务 / 环境 / swagger / 模块 / task**。环境层（us/cn/eu）将三个独立部署的用户数据和配置隔离，同一接口在不同环境的用户行为差异显著，必须分开生成 case。
- **多平台服务六层：服务 / 平台 / 环境 / 模块 / task**。平台在环境之上，因为不同平台的规则逻辑和测试数据完全不同，是比环境更高维度的划分。调用 skill 时若传入平台参数，自动使用多平台目录结构；无平台参数则使用标准结构。
- **按服务组织，不是按平台**：一个服务可能对应**多个 Swagger**（如 mainapi 服务下同时有 `Amazon.Advertising.Api` 和 `PacvueMainApi` 两个 Swagger）。
- **config.json 是环境级**：每个环境有独立的 `single-api/<服务>/<环境>/config.json`（标准）或 `single-api/<服务>/<平台>/<环境>/config.json`（多平台），含该环境的 token、profile_id、base_urls 等；不同环境的 base_url 域名不同，不能共用。
- **服务名**先查 `single-api/services.json` 反查（见"输入"第二步）：命中用表里的名，未命中问用户后回写；默认一 swagger 一服务、名=`info.title`。
- **swagger 层名**取该接口来源 spec 的 `info.title`（也是 `endpoints-<title>.json` 的 title）。多平台服务无 swagger 层，模块名直接取接口 tag。
- **模块名**取接口路径首段（如 `/api/Target/*` → `Target`，`/api/Targeting/V3/*` → `Targeting`）。
- **endpoints-*.json 放 `single-api/` 根**，文件名取各 Swagger 的 `info.title`（一个 Swagger 一份，与环境/服务/模块正交，Swagger 结构不分环境）。

---

## 🔴 铁律

1. **Swagger 是结构权威**：字段类型、必填性、枚举值以 Swagger 为准，ES 只提供真实值样本
2. **禁止猜参数值**：无 Swagger example 且 ES 无样本的字段，值填 `"[NEEDS_REAL_VALUE]"` 并在末尾列出待补清单
3. **动态 ID 必须变量化**：数字 ID / timestamp 替换为 `{{var}}`，不得硬编码
4. **每次新建目录**：`single-api/<服务>/<swagger>/<模块>/task-<YYYY-MM-DD-HH-MM-SS>/`，禁止复用
5. **config.json 跟服务走**：位于 `single-api/<服务>/config.json`，一个服务一份（含该服务所有 base_url）
6. **服务身份先查 `single-api/services.json`**：swagger→服务 的映射维护在此表，命中就不问用户；未命中才问并回写
7. **产物只有 cases.json、endpoints.json、services.json**：禁止生成其他文件

---

## 输入（运行时向用户逐步确认）

**第一步：用户提供 Swagger URL**

用户只需提供一个或多个 Swagger 文档的 URL（index.html 或 swagger.json 均可），无需事先指定接口。

**第二步：查 `single-api/services.json` 反查服务（🔴 先查表，别问）**

服务身份的锚点是 **GitHub 后端服务（部署单元）**，一个服务可能对应多个 Swagger、共用一个 ES 索引和一份 config。这个归并关系 Swagger 里推不出，维护在 `single-api/services.json`：

```json
{
  "<服务名>": {
    "github_repo": "<仓库名>",
    "swaggers": [
      { "title": "<info.title>", "url": "<swagger json url>" }
    ],
    "platforms": ["amazon", "tiktok", "walmart"],
    "es_index": {
      "us": "<US ES 索引，如 amazon-access-*>",
      "cn": "<CN ES 索引，如 cn-amazon-access-*>",
      "eu": "<EU ES 索引，如 eu-amazon-access-*>"
    },
    "config": "single-api/<服务名>/{env}/config.json",
    "es": {
      "path_field": "<接口路径字段，如 apiEndpoint.keyword / urlReferrer.keyword>",
      "method_field": "method.keyword",
      "body_field": "body",
      "body_is_json_string": true,
      "clientid_exclude": [62, 3186],
      "assertion_l1": { "code": 200, "success": true },
      "platform_filter": null
    }
  }
}
```

- `swaggers`：title 和 url 配对，取代原来的 `swagger_titles` + `swagger_urls` 两个并列数组
- `platforms`：仅多平台服务有此字段（如 rule-api）；无此字段则走标准目录结构，config 路径含 `{env}`；有此字段则走多平台目录结构，config 路径含 `{platform}/{env}`
- 🔴 `es`：**该服务所有 ES 查询差异集中在此块**（详见 Phase 2.1），新增服务只需填这里，正文不再逐服务列举：
  - `path_field` / `method_field` / `body_field`：ES 索引里对应的字段名（服务间不通用，首次接入需探测确认）
  - `body_is_json_string`：`body` 是 JSON 字符串（需二次 `ConvertFrom-Json`，如 mainapi）还是已是对象（`_source` 直接取，如 rule-api）
  - `clientid_exclude`：查询时固定 `must_not` 排除的测试账号 clientId
  - `assertion_l1`：该服务 Happy Path 的 L1 断言模板（mainapi 有 `success` 字段，rule-api 只有 `code`）
  - `platform_filter`：多平台服务的平台过滤方式（单平台服务为 `null`）。`{"get":"all","post":"queryString:productLine=<platform>"}` 表示 GET 用全平台流量、POST 按 `queryString` 过滤当前平台

**流程**：
1. 读 `single-api/services.json`（不存在则视为空表）
2. 用用户给的 swagger URL / 扫描出的 `info.title` 去匹配某条目的 `swaggers[].url` / `swaggers[].title`
   - **命中** → 直接得到服务名、`es_index`（对象）、`config` 路径模板，**不再向用户提问服务归属**，进环境确认
   - **未命中** → 只问一次：`"这些 swagger 属于哪个服务？(默认按各自 info.title 分开；若同属一个服务请给统一名，如 mainapi)"`，收到后**追加/更新 `services.json`**，下次自动命中
3. **确认目标平台**（仅多平台服务）：若服务含 `platforms` 字段且用户请求中已明确平台，直接使用；否则反问一次列出可选项。config 路径替换 `{platform}` 为实际平台名
4. **确认目标环境**：若用户请求中已明确环境（如"CN 环境"、"eu"），直接使用；否则反问一次：`"为哪个环境生成 case？us / cn / eu"`。根据环境从 `es_index.<env>` 取对应索引，config 路径替换 `{env}` 为实际环境名
5. 默认规则：一个 swagger 一个服务，服务名 = `info.title`；仅当用户显式归并时才多 swagger 合一

ES 连接信息已固定，无需用户提供：
- **Kibana 地址**：`https://logs.pacvue.com`
- **用户名**：`watcher`
- **密码**：`kY9GErML%luQTorm`
- **访问方式**：PowerShell `Invoke-RestMethod` + Basic Auth
- **ES 索引**：从 `services.json` 的 `es_index` 读，不再每次询问

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
node ".claude/skills/swagger-api-case/scripts/parse_swagger.js" `
  "$env:TEMP\swagger_<服务名>.json" `
  "C:/AI engineering/single-api/ai_api/single-api/endpoints-<title>.json"
```

> 脚本源码见 `scripts/parse_swagger.js`。输出：写入 endpoints 文件 + 按模块分组的汇总表。

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

### 2.1 ES 字段与查询参数（读 services.json.es）

🔴 **服务间的 ES 差异全部读 `services.json.<服务>.es`，本文不再逐服务列举**。查询前从该块取：`path_field`（接口路径字段）、`method_field`、`body_field`、`body_is_json_string`、`clientid_exclude`、`assertion_l1`、`platform_filter`。字段含义见"输入"章节的 schema 说明。

- mainapi：`path_field=apiEndpoint.keyword`、`body_is_json_string=true`（body 是字符串，需二次 `ConvertFrom-Json`）
- rule-api：`path_field=urlReferrer.keyword`、`body_is_json_string=false`（body 已是对象，`_source` 直接取）

**新服务首次接入**：`es` 块为空时先探测字段，确认后**回写 `services.json.<服务>.es`**，下次直接读：
```powershell
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("watcher:kY9GErML%luQTorm"))
$headers = @{ "Authorization" = "Basic $b64"; "kbn-xsrf" = "true" }
Invoke-RestMethod -Uri "https://logs.pacvue.com/api/index_patterns/_fields_for_wildcard?pattern=<索引名>&meta_fields=_source" -Headers $headers | ConvertTo-Json -Depth 3
```

🔴 **多平台服务的场景挖掘按 HTTP 方法分治**（由 `es.platform_filter` 驱动）：这类服务用请求 header 区分平台，ES access log **不索引请求 header**，但 **POST 请求会把 productLine 带在 query string 上**（ES `queryString` 字段可见，如 `productLine=tiktok`），GET 请求则 `queryString` 为空——两类接口场景来源不同：

| 方法 | ES 能否区分平台 | 场景挖掘用的样本范围 |
|------|------|------|
| **GET** | ❌ 不能（productLine 只在 header，ES 未索引，`queryString` 为空） | **全平台流量**：不加 productLine 过滤，用该接口在 ES 里的全部真实调用挖场景 |
| **POST** | ✅ 能（`queryString` 含 `productLine=xxx`） | **当前测试平台的流量**：加 `{"match_phrase":{"queryString":"productLine=<当前平台>"}}` 过滤，只用该平台的真实调用挖场景 |

- **POST 接口**该平台若无流量则按"无 ES 流量"处理（见 2.3 / Phase 4 占位规则）。
- **平台覆盖仍是强制枚举，与 ES 频率无关**：无论 GET/POST，`services.json.<服务>.platforms` 里的每个平台都要单独生成一遍 case（同一份 cases.json 指向该平台的 `config.json`）。ES 频率只决定"某个接口/某个平台下写哪几条 body 场景"，不决定"要不要覆盖这个平台"。

### 2.2 查询目标接口日志

🔴 **统一用 `scripts/query_es.ps1`**（内建 `/internal/search/es` 调用 + GET/POST 平台过滤 + clientId 排除，避免手写查询出错）。参数从 `services.json.<服务>.es` 取：

```powershell
pwsh ".claude/skills/swagger-api-case/scripts/query_es.ps1" `
  -Index     <es_index.<env>，如 rule-api-access-*> `
  -Path      <endpoint_path> `
  -Method    <GET|POST> `
  -PathField <es.path_field，如 urlReferrer.keyword> `
  [-Platform <当前平台，仅多平台服务传>]
# 只要命中数加 -CountOnly；默认返回 500 条样本的 body
```

脚本已内建两条关键规则，无需手动处理：
- **平台过滤**（`es.platform_filter`）：POST + `-Platform` → 自动加 `queryString: productLine=<平台>`；GET 或未传平台 → 不加（GET 的 `queryString` 为空，加了会误判零流量）。
- **clientId 排除**（`es.clientid_exclude`，默认 `62,3186`）：clientId=3186（superAdmin0913 等测试账号）、62（内部研发账号）为纯测试 client，固定排除防污染。

🔴 **body 解析看 `es.body_is_json_string`**：`true`（mainapi）需对返回的 body 再 `ConvertFrom-Json`；`false`（rule-api）已是对象直接用。**L1 断言用 `es.assertion_l1`**：mainapi=`{"code":200,"success":true}`，rule-api=`{"code":200}`（无 `success`），不要跨服务照抄。

取出的每条记录即为真实入参，进入 2.3 分析。

**🔴 若命中数 < 10**：脚本默认已用 `now-90d`；仍不足则用全部命中条数，并在对话中注明"样本较少，场景覆盖可能不全"。

### 2.3 分析真实入参，归纳用户场景

🔴 **不得直接用频率统计替代场景分析**。要阅读每条入参的实际内容，理解用户在做什么操作，再归纳成有业务意义的场景。

🔴 **硬规则是"占比 ≥1% 的真实场景全覆盖"，不是"凑够 3 条"**。case 数 = 真实存在的 ≥1% 场景数，有几个写几个：

- **3 条是争取目标，不是硬性下限**：先尽力从样本里挖真实业务差异（不同 recordType / campaignType / 分页 / 过滤组合 / 排序等）；只要是样本里真实出现且占比 ≥1% 的差异，就各自成 case。
- **🔴 绝不为凑数编造**：若某接口真实调用就只有 1~2 种模式（如空 body 的日志/列表接口、单一 100% 场景），就只写这 1~2 条真实 case。**禁止**用样本里不存在的 recordType/参数组合硬造第 3 条来凑数——宁可 1 条真实，不要 3 条有假。
- 识别出的有业务差异场景越多越好，全部生成 case，不合并、不丢弃。
- case 少于 3 条时，在对话中说明"该接口真实调用仅 N 种模式，已全覆盖"，让用户知道是真实情况而非漏测。

**场景归纳方法（以调用频率为核心）**：

场景不是从字段差异推导出来的，而是从**用户最常用的入参组合**归纳出来的。步骤：

1. **让样本自己暴露维度**：通读 500 条样本，观察这个接口里哪些字段的取值在请求之间**实际发生了变化**——变化的字段才是本接口的划分维度。不要拿预设的字段清单去套；不同接口的维度完全不同，以当前样本为准。
2. **统计入参组合频率**：按上一步发现的维度字段的取值组合分组，统计每种组合出现的次数和占比
3. **按频率排序**：出现次数最多的组合 → 场景1，次多 → 场景2，以此类推
4. **判断是否值得独立成场景**：占比 **≥ 1%** 的组合**必须**独立成场景并生成 case（含占比恰为 1% 的）；仅占比 **< 1%** 的组合才舍弃（除非它代表了高频场景没有的独立业务意图，则仍要覆盖）。不再按 5%/2% 做合并——只要占比 ≥ 1% 一律覆盖，不合并进高频场景。
5. **用该场景最典型的一条真实入参**作为 case 的 `request_body`，动态字段变量化后直接使用

场景描述中注明频率：
```
代表条数：n 条，占比约 xx%（500条样本中）
```

场景覆盖规则（唯一标准：占比 ≥ 1%）：
- 占比 ≥ 1% 的场景**全部必须覆盖**，一个不漏（无论高频低频，1% 是硬门槛）
- 占比 < 1% 的场景：默认舍弃；仅当代表了 ≥1% 场景没有覆盖到的独立业务意图时才额外补上
- case 数 = 覆盖到的真实场景数，可能不足 3 条：若接口真实调用模式本就少（如单一 100% 场景），如实只写真实的，**不编造凑数**（见上方 case 数下限说明）

**归纳输出格式**（每个场景一段）：

```
### 场景N：<业务描述>
特征：<关键字段组合>
代表条数：[编号列表]，占比约 xx%
含义：<用户在界面上做了什么操作>
```

**归纳完成后**，每个场景对应一个 Happy Path case，用该场景的真实入参（动态字段变量化）填写 `request_body`。场景数即 Happy Path case 数，一一对应，不合并、不删减。

- ES 查询失败或无结果：记录原因，告知用户，终止本次生成

**🔴 占比必须写进 case `description`**：每个 Happy Path case 的 `description` 末尾固定追加 `500条随机样本中占比约xx%（n次）。`，供 Phase 5 场景覆盖列提取。**漏写会导致 Excel 场景覆盖显示不出占比**。

**旧 case 占比补算（`scripts/backfill_pct.py`）**：若已有 cases.json 缺占比，用此脚本按现有 case 的判别签名重新查 ES 统计并回填：

```powershell
# 标准服务（mainapi，默认 amazon-access-*）
python ".claude/skills/swagger-api-case/scripts/backfill_pct.py" `
  "single-api/<服务>/<环境>/<swagger>/<模块>/task-<timestamp>/cases.json"

# 多平台服务（rule-api，需指定 ES 索引）
python ".claude/skills/swagger-api-case/scripts/backfill_pct.py" `
  "single-api/rule-api/<平台>/<环境>/<模块>/task-<timestamp>/cases.json" `
  --es-index "rule-access-*"
```

脚本按 `(接口路径, HTTP方法)` 分组、增/查/改/删全部统计，判别签名与归类规则见脚本 docstring。**Health / ES 无记录端点**无流量则不写占比（Excel 场景覆盖只显示场景标签，不显示 `— xx%`）。

---

## Phase 3 — 生成 cases.json

**创建目录**：`single-api/<服务>/<环境>/<swagger>/<模块>/task-<YYYY-MM-DD-HH-MM-SS>/`（如 `single-api/mainapi/us/PacvueMainApi/Targeting/task-2026-08-13-12-00-55/`）

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

🔴 **断言路径必须写成嵌套对象，不能用点号路径**：run-cases.py 的断言引擎**不按 `.` 拆分 key**，`"data.successCount"` 会被当成字面顶层 key → 永远 `undefined`。嵌套字段一律逐层嵌套：
- ✅ `{"data": {"successCount": {"$gte": 1}}}`
- ❌ `{"data.successCount": {"$gte": 1}}`（永远 undefined，误判 FAIL）

**L2（基于实际响应结构，Phase 4 探测后补充）**：
- 返回结构为 `data: {list:[], pageInfo:{}}` → 加 `"data": {"pageInfo": {"$not_empty": true}}`
- 返回结构为 `data: {Data:[...]}`（分页列表）→ 加 `"data": {"Data": {"$is_array": true}}`
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
        "base_url": "<按来源 swagger 选，见下方 base_url 规则，如 {{INDBASEURL}} / {{BASEURL}}>",
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

**base_url 选择规则**（🔴 按 **endpoint 来源的 swagger** 选，不是按路径前缀）：

同一服务下多个 swagger 的路径可能都以 `/api/` 开头，**不能用路径前缀判断**。要看该 endpoint 是从哪个 swagger 扫出来的，映射到对应 base_url 变量：

| endpoint 来源 swagger（info.title） | base_url 变量 | 实际地址 |
|---|---|---|
| `Amazon.Advertising.Api` | `{{INDBASEURL}}` | `amazon-advertising-api/api/` |
| `PacvueMainApi` | `{{BASEURL}}` | `pacvuemainapiv2/api/` |

其他服务的 base_url 变量（按需在 config.json 的 `base_urls` 里补充）：`{{META}}`(meta-api)、`{{DAYPARTING}}`(micro-api-v2)、`{{FILTER_COLUMN}}`(filter-column)、`{{AIURL}}`(ai-api)、`{{RULEBASEURL}}`(rule-api，实际地址 `rule-api/`，路径不带 `/api/` 前缀，直接拼 `RULEBASEURL` + path)。

🔴 **生成前先确认**：该 endpoint 在哪个 `endpoints-<title>.json` 里 → 对应 base_url 变量 → config.json 的 `base_urls` 里必须有这个变量。

---

## Phase 3.5 — 写操作类 case 必须自清理 + 可重复（🔴 强制）

**判定为写操作类**：接口名/语义属于 **创建 / 编辑 / 批量操作**（Create、Add、Update、BulkUpdate、Copy、Delete、Archive、状态变更、出价变更等）。查询类（Get/Report/Chart/Total/PageData）不适用本节。

### 铁律

1. **写操作 case 必须成对**：主操作步骤 + 后置逆操作步骤，把产生/改动的数据还原，禁止在测试账号留残留。
   - 创建 ↔ 归档（archive）
   - 状态变更（如 paused）↔ 改回原 state
   - 出价变更 ↔ 改回原 bid
   - 批量操作 ↔ 逆向批量还原

2. **Amazon 实体只能 archive，不能物理删**：清理创建类数据 = 调状态接口把 `state` 置为 `archived`，这就是业务层"删除"。

3. **用 `extract_vars` 抓取新建实体 ID**，后置步骤引用，**禁止硬编码 ID**。
   - 提取路径支持数组下标，如 `data.result[0].APIResult[0].entityId`
   - 框架自动把提取值注入后续步骤的 `{{var}}`（同一 case 内跨步骤有效）

4. **断言用业务成功信号**：写操作断言 `"data": {"successCount": {"$gte": 1}}`（嵌套写法，见 Phase 3 断言路径规则；或对应的真实成功计数字段），**不能只断言 `code:200`**——很多写接口 HTTP/业务 code 都是 200 但实际 `success 0`（如 bid 超预算一半、谓词类型错误、重复创建）。

5. **保证幂等可重跑**：后置清理后，同参数必须能再次执行。
   - 创建类：归档后同 ASIN/关键词可再次创建（已验证 Amazon 支持）
   - 编辑类：先在前置/主步骤存原值，后置步骤还原
   - 生成后**连跑 2 次**验证全 PASS，才算通过

### case 模板与值探测

🔴 可直接套用的**写操作 case JSON 模板**（创建 + 后置归档）与**写操作值探测清单**（真实层级 / bid 约束 / 枚举值以 ES 为准）见 `references/write-case-template.md`，生成写操作 case 前先读该文件。

---

## Phase 4 — 执行 cases.json 并产出 report.json

### 4.1 前置：去除 BOM

PowerShell 生成的文件带 UTF-8 BOM，`json.load` 会报错，执行前先修复（脚本见 `scripts/fix_bom.py`）：

```bash
python ".claude/skills/swagger-api-case/scripts/fix_bom.py" \
  single-api/<服务>/<环境>/<swagger>/<模块>/task-<timestamp>/cases.json \
  single-api/<服务>/<环境>/config.json
```

### 4.2 执行

```bash
python "C:/AI engineering/rule-modules-web-master/rule-modules-web-master/.claude/skills/api-case-generate/api-case-run/scripts/run-cases.py" \
  --cases single-api/<服务>/<环境>/<swagger>/<模块>/task-<timestamp>/cases.json \
  --config single-api/<服务>/<环境>/config.json \
  --out    single-api/<服务>/<环境>/<swagger>/<模块>/task-<timestamp>/report.json
```

🔴 **注意事项**：
- `--config` 必须指向该服务的 `single-api/<服务>/config.json`，不得用默认的 `api-case-work/config.json`
- cases 的 `path` 字段**不含 `/api/` 前缀**（已在生成时去掉），`INDBASEURL` 末尾有 `/api/`，两者拼接才正确
- token 会过期（约 10 小时），执行前确认 config.json 里 token 有效；脚本检测到 401 会自动用 `auth` 配置重新登录

### 4.3 分析结果

按接口聚合 PASS/FAIL（脚本见 `scripts/summarize_report.py`）：

```bash
python ".claude/skills/swagger-api-case/scripts/summarize_report.py" \
  single-api/<服务>/<环境>/<swagger>/<模块>/task-<timestamp>/report.json
```

**常见失败原因**：

| 现象 | 原因 | 处理 |
|------|------|------|
| HTTP 400 | 请求体结构异常（Filters 反序列化失败） | 删除该场景的 case |
| HTTP 200 但 FAIL | `data` 返回空列表，`$not_empty` 断言不过 | 断言改为 `$is_array` 允许空 |
| HTTP 401 | token 过期 | 重新登录刷新 token |
| HTTP 403 `toMarket contains illegal characters` | `{{to_market}}` 变量未替换（不经 run-cases.py 直接发请求时出现） | 必须通过 run-cases.py 执行 |
| HTTP 200 + `success:true` 但写操作 `successCount=0` / `success 0` | 写接口业务层未生效：bid 超预算一半 / 谓词类型(如 SD `type`)错误 / 同参重复创建 / 规则托管广告组拒绝 | 查看 `data.result[].APIResult[].message` 或 `ErrorMessages` 定位；修正 bid/枚举值/目标层级；确保后置清理已归档避免重复 |
| 写操作 case 第二次跑失败（首次 PASS） | 未加后置清理，实体已存在导致重复创建失败 | 按 Phase 3.5 补后置逆操作步骤，连跑 2 次验证 |

---

## Phase 5 — 写入 Excel 统计表（🔴 每次执行后必做）

Excel 文件按服务独立存放：`single-api/<服务>/swagger_modules.xlsx`（update_excel.py 从 cases 路径自动推断，无需手动指定）。

同时写入两个目标：

| 目标 | Sheet | 内容 |
|------|-------|------|
| **5.1 模块汇总** | `模块汇总` | 按 `环境+Swagger+模块` 匹配行，写 Case数 / 通过率 / 接口覆盖率 |
| **5.2 接口级覆盖** | `Amazon.Advertising.Api` / `PacvueMainApi` 等 | 按 `接口路径` 匹配行，写三列（均带环境后缀）：`场景数(env)` / `通过率(env)` / `场景覆盖(env)` |

**5.2 三列含义**（env 后缀区分环境，如 `场景数(us)`）：
- `场景数(env)`：该接口在本次生成的 case 数（= 场景数），从 report 按接口路径统计
- `通过率(env)`：该接口所有 case 的通过率（passed/total）
- `场景覆盖(env)`：多行文本，列出每个场景的标签 + 占比，格式 `场景N: 描述 — xx%`
- 未生成 case 的接口三列留空，一眼可见哪些接口还没覆盖

**一条命令搞定**（脚本源码见 `scripts/update_excel.py`）：

```powershell
python ".claude/skills/swagger-api-case/scripts/update_excel.py" `
  --cases    "single-api/<服务>/<环境>/<swagger>/<模块>/task-<timestamp>/cases.json" `
  --report   "single-api/<服务>/<环境>/<swagger>/<模块>/task-<timestamp>/report.json" `
  --endpoints "single-api/endpoints-<swagger-title>.json" `
  --swagger-title "<swagger info.title，如 Amazon.Advertising.Api>" `
  --module   "<模块名，如 SupplementData>" `
  --env      "<环境，如 us / cn / eu>"
```

**接口覆盖率计算**：  
`api_covered` = cases.json 中不重复的 `path` 数量（一个接口多个场景只算 1）  
`api_total` = `endpoints-<title>.json` 中该模块的接口总数

**场景覆盖格式**（从 case `name`/`description` 自动提取）：
```
场景1: Campaign+日期过滤 Campaign汇总含广告组数 — 52.6%
场景2: Campaign+日期过滤 CostControl输出不含AdGroupCount — 18.8%
...
```

---

## 交付物

| 文件 | 说明 |
|------|------|
| `single-api/services.json` | 🔴 服务映射表：swagger(title/url) → 服务名 / ES 索引 / config，命中免询问，未命中回写 |
| `single-api/endpoints-<info.title>.json` | 当前 Swagger 全量有效接口列表，文件名取 spec 的 `info.title`（每次覆盖，放根目录） |
| `single-api/<服务>/<环境>/config.json` | 🔴 环境级执行配置（token、profile_id、base_urls 等），us/cn/eu 各一份 |
| `single-api/<服务>/<环境>/<swagger>/<模块>/task-<timestamp>/cases.json` | 目标接口的测试 case |
| `single-api/<服务>/<环境>/<swagger>/<模块>/task-<timestamp>/report.json` | 执行结果报告 |
| `single-api/<服务>/swagger_modules.xlsx`（`模块汇总` sheet） | 更新 Case数 / 通过率 / 接口覆盖率三列，每个服务独立一份 |

对话中额外输出**待补清单**（若有 `[NEEDS_REAL_VALUE]` 字段）。
